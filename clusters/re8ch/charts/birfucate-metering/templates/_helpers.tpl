{{- define "birfucate-metering.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- define "birfucate-metering.fullname" -}}
{{- if .Values.fullnameOverride }}{{ .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}{{ else }}{{ include "birfucate-metering.name" . }}{{ end }}
{{- end }}
{{- define "birfucate-metering.labels" -}}
app.kubernetes.io/name: {{ include "birfucate-metering.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
{{- define "birfucate-metering.localDNSPodSpec" -}}
{{- if .Values.localDNS.enabled }}
dnsPolicy: None
dnsConfig:
  nameservers: [{{ .Values.localDNS.clusterIP | quote }}]
  searches: [{{ .Release.Namespace }}.svc.cluster.local, tenant-infrastructure.svc.cluster.local, svc.cluster.local, cluster.local]
  options: [{name: ndots, value: "5"}]
{{- end }}
{{- end }}
