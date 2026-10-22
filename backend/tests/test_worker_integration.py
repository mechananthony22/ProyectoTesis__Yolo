"""Real Redis + Celery + PostgreSQL roundtrip, enabled in CI only."""
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
import pytest
from django.db import connection
from django.conf import settings
from config.celery import app
from apps.research.models import Dataset, Job, ImageVariant
from apps.research.services import import_images
from .helpers import upload

@pytest.mark.skipif(os.getenv('REDIS_INTEGRATION') != '1', reason='Requires Redis and PostgreSQL services; enabled in CI')
@pytest.mark.django_db(transaction=True)
def test_real_worker_processes_preprocessing_job(user, tmp_path):
    assert connection.vendor == 'postgresql'
    dataset=Dataset.objects.create(owner=user,name='Redis worker fixture')
    import_images(dataset,[upload()],user)
    image=dataset.images.get()
    job=Job.objects.create(owner=user,kind='preprocessing',config={'images':[str(image.pk)],'size':640})
    queue='smoke-'+uuid.uuid4().hex
    env={**os.environ,'DJANGO_SETTINGS_MODULE':'config.ci_settings','POSTGRES_DB':connection.settings_dict['NAME'],'MEDIA_ROOT':str(settings.MEDIA_ROOT)}
    backend=Path(__file__).resolve().parents[1]
    with (tmp_path/'worker.log').open('w+') as log:
        worker=subprocess.Popen([sys.executable,'-m','celery','-A','config','worker','-P','solo','--concurrency=1','--without-gossip','--without-mingle','--without-heartbeat','-Q',queue,'--loglevel=warning'],cwd=backend,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            task=app.send_task('apps.research.tasks.preprocess',args=[str(job.pk)],queue=queue)
            deadline=time.monotonic()+40
            while time.monotonic()<deadline:
                job.refresh_from_db()
                if job.state in ['succeeded','failed']: break
                if worker.poll() is not None: break
                time.sleep(.25)
            if job.state != 'succeeded':
                log.seek(0)
                pytest.fail(f'Worker did not complete job: {job.state}. {job.error}. Logs: {log.read()[-3000:]}')
            assert ImageVariant.objects.filter(job=job,image=image).count()==1
            assert job.progress==100
            task.forget()
        finally:
            worker.terminate()
            try: worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker.kill();worker.wait(timeout=5)
