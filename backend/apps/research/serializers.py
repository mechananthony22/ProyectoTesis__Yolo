from rest_framework import serializers
from . import models as m
from .validation import check_boxes

class DatasetSerializer(serializers.ModelSerializer):
    image_count=serializers.IntegerField(source='images.count',read_only=True)
    class Meta:
        model=m.Dataset
        fields=['id','name','description','source','license','archived','owner','created_at','image_count']
        read_only_fields=['owner']
class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model=m.ImageAsset
        exclude=['file']
        read_only_fields=['dataset','name','sha256','perceptual_hash','width','height','size','state','annotations','revision','reviewed_by','reviewed_at','quality']
class AnnotationInput(serializers.Serializer):
    annotations=serializers.JSONField()
    state=serializers.ChoiceField(choices=['pending','healthy','lesion','discarded'])
    revision=serializers.IntegerField(min_value=0)
    note=serializers.CharField(required=False,allow_blank=True)
    def validate_annotations(self,value): return check_boxes(value)
class VersionSerializer(serializers.ModelSerializer):
    dataset_name=serializers.CharField(source='dataset.name',read_only=True)
    count=serializers.SerializerMethodField()
    class Meta:
        model=m.DatasetVersion
        exclude=['archive']
        read_only_fields=['__all__']
    def get_count(self,obj): return len(obj.manifest)
class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model=m.Job
        fields='__all__'
class TrainingSerializer(serializers.ModelSerializer):
    job=JobSerializer(read_only=True)
    class Meta:
        model=m.TrainingRun
        fields='__all__'
class ModelSerializer(serializers.ModelSerializer):
    metrics=serializers.JSONField(source='run.metrics',read_only=True)
    class Meta:
        model=m.AIModel
        exclude=['weights']
class InspectionSerializer(serializers.ModelSerializer):
    job=JobSerializer(read_only=True)
    model_name=serializers.CharField(source='model.name',read_only=True)
    has_annotated=serializers.SerializerMethodField()
    class Meta:
        model=m.Inspection
        exclude=['original','annotated']
    def get_has_annotated(self,obj): return bool(obj.annotated)
class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model=m.ImageVariant
        exclude=['file']
class EvaluationSerializer(serializers.ModelSerializer):
    sample_count=serializers.IntegerField(source='samples.count',read_only=True)
    class Meta:
        model=m.Evaluation
        fields='__all__'
        read_only_fields=['owner','locked','metrics','job']
class TrainingInput(serializers.Serializer):
    version=serializers.UUIDField()
    architecture=serializers.ChoiceField(choices=['yolov8n.pt','yolov8s.pt'])
    epochs=serializers.IntegerField(min_value=1,max_value=500,default=50)
    batch=serializers.IntegerField(min_value=1,max_value=64,default=8)
    imgsz=serializers.ChoiceField(choices=[640,800],default=640)
    lr0=serializers.FloatField(min_value=0.000001,max_value=0.1,default=0.01)
    optimizer=serializers.ChoiceField(choices=['auto','SGD','Adam','AdamW'],default='auto')
    weight_decay=serializers.FloatField(min_value=0,max_value=0.1,default=0.0005)
    patience=serializers.IntegerField(min_value=0,max_value=100,default=20)
    seed=serializers.IntegerField(min_value=0,max_value=2**31-1,default=42)
    fliplr=serializers.FloatField(min_value=0,max_value=1,default=0.5)
    degrees=serializers.FloatField(min_value=0,max_value=30,default=10)
    hsv_v=serializers.FloatField(min_value=0,max_value=0.4,default=0.2)
class PreprocessingInput(serializers.Serializer):
    images=serializers.ListField(child=serializers.UUIDField(),min_length=1,max_length=200)
    size=serializers.ChoiceField(choices=[640,800],default=800)
    brightness=serializers.FloatField(min_value=0.5,max_value=1.5,default=1)
    contrast=serializers.FloatField(min_value=0.5,max_value=1.5,default=1)
    crop=serializers.ListField(child=serializers.FloatField(min_value=0,max_value=1),min_length=4,max_length=4,default=[0,0,1,1])
    def validate_crop(self,v):
        if v[2]-v[0]<0.02 or v[3]-v[1]<0.02: raise serializers.ValidationError('Recorte inválido o demasiado pequeño.')
        return v
