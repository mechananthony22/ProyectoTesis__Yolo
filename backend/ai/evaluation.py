from math import comb
from statistics import mean

def classification(truth, predicted):
    tp=sum(t and p for t,p in zip(truth,predicted)); fp=sum(not t and p for t,p in zip(truth,predicted))
    fn=sum(t and not p for t,p in zip(truth,predicted)); tn=sum(not t and not p for t,p in zip(truth,predicted))
    return {'n':len(truth),'tp':tp,'fp':fp,'fn':fn,'tn':tn,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,'accuracy':(tp+tn)/len(truth) if truth else None}

def paired(truth, system, manual, system_times, manual_times):
    b=sum(s==t and m!=t for t,s,m in zip(truth,system,manual))
    c=sum(s!=t and m==t for t,s,m in zip(truth,system,manual))
    from scipy.stats import binomtest, wilcoxon
    p=float(binomtest(b,b+c,p=0.5).pvalue) if b+c else 1.0
    differences=[m-s for s,m in zip(system_times,manual_times)]
    wp=float(wilcoxon(differences,method='auto').pvalue) if any(differences) else 1.0
    return {'system':classification(truth,system),'manual':classification(truth,manual),'mcnemar_exact_p':p,'wilcoxon_p':wp,'mean_system_ms':mean(system_times),'mean_manual_ms':mean(manual_times),'note':'Análisis pareado exploratorio por fruto y participante; requiere interpretar protocolo, tamaño muestral y comparaciones múltiples.'}
