import os
import pytz
import kopf
import random
from os import getenv
from datetime import datetime
from kubernetes import client as kube_client

API_GROUP = 'abriment.dev'
API_VERSION = 'v1'

CHECK_INTERVAL = int(getenv('CHECK_INTERVAL', 300))
TBSC_NAME_ANNOTATION_KEY = getenv('TBSC_NAME_ANNOTATION_KEY', f'tbscs.{API_GROUP}/name')
DEFAULT_TIMEZONE = getenv('DEFAULT_TIMEZONE', "Asia/Tehran")


class TimeBasedScalingController:
    def __init__(self, namespace):
        self.namespace = namespace
        self.custom_api = kube_client.CustomObjectsApi()

    def read(self, name):
        return self.custom_api.get_namespaced_custom_object(
            group=API_GROUP,
            version=API_VERSION,
            plural='tbscs',
            name=name,
            namespace=self.namespace
        )


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.persistence.finalizer = f'finalizers.{API_GROUP}/TimeBasedScalingController'
    settings.peering.clusterwide = True
    settings.peering.priority = random.randint(0, 32767)
    settings.peering.stealth = True
    settings.posting.enabled = False


def evaluate_replicas(tbsc: dict) -> int:
    scheduling_config = tbsc['spec'].get('schedulingConfig', [])
    default_replicas = tbsc['spec'].get('defaultReplicas', 1)
    priorities = []

    for sc in scheduling_config:
        sc_data = sc.get('spec', sc)  # Handle both inline and nested `spec`
        start_time = sc_data['startTime']
        end_time = sc_data['endTime']
        replicas = sc_data['replicas']

        tz_name = sc_data.get('timeZone', DEFAULT_TIMEZONE)
        try:
            timezone = pytz.timezone(tz_name)
        except Exception:
            timezone = pytz.timezone(DEFAULT_TIMEZONE)

        now = datetime.now(tz=timezone).time()
        start = datetime.strptime(start_time, '%H').time()
        end = datetime.strptime(end_time, '%H').time()

        if (start < end and start < now < end) or (start > end and (now > start or now < end)):
            priorities.append((start, replicas))

    return sorted(priorities, key=lambda x: x[0])[0][1] if priorities else default_replicas


def handle_scaling(app_kind: str, meta, spec, name: str, namespace: str, logger):
    tbsc_name = meta['annotations'].get(TBSC_NAME_ANNOTATION_KEY)
    if not tbsc_name:
        logger.warning("No TBSC name annotation found.")
        return

    tbsc_instance = TimeBasedScalingController(namespace)

    try:
        tbsc = tbsc_instance.read(tbsc_name)
        desired_replicas = evaluate_replicas(tbsc)
        current_replicas = spec.get('replicas')

        if desired_replicas != current_replicas:
            scale(app_kind, name, namespace, desired_replicas)
            logger.info(f"Scaled {app_kind} {name} to {desired_replicas} replicas.")
    except Exception as e:
        logger.error(f"Failed to process scaling for {app_kind} {name}: {e}")


@kopf.timer('deployments', interval=CHECK_INTERVAL, annotations={TBSC_NAME_ANNOTATION_KEY: kopf.PRESENT}, timeout=60)
def deployment_scaling_handler(meta, spec, name, namespace, logger, **kwargs):
    handle_scaling('deployment', meta, spec, name, namespace, logger)


@kopf.timer('statefulsets', interval=CHECK_INTERVAL, annotations={TBSC_NAME_ANNOTATION_KEY: kopf.PRESENT}, timeout=60)
def statefulset_scaling_handler(meta, spec, name, namespace, logger, **kwargs):
    handle_scaling('statefulset', meta, spec, name, namespace, logger)


def scale(app_kind: str, name: str, namespace: str, replicas: int):
    app_client = kube_client.AppsV1Api()
    body = {"spec": {"replicas": replicas}}
    patch_methods = {
        'deployment': app_client.patch_namespaced_deployment,
        'statefulset': app_client.patch_namespaced_stateful_set,
    }
    patch_method = patch_methods.get(app_kind)
    if patch_method:
        patch_method(name, namespace, body)
