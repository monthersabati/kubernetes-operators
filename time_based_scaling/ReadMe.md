# Time-Based Scaling Operator

This operator automatically scales Kubernetes deployments based on a time-based schedule. It allows you to define schedules for scaling your deployments up or down, based on the time of day or other time-based criteria.

## Overview

The Time-Based Scaling Operator (TBSC) is a Kubernetes operator built using the Kopf framework. It watches for custom resources of type `TimeBasedScalingController` (TBSC) and automatically scales the associated deployments according to the schedules defined in the TBSC resource.

## Features

*   **Time-based scaling:** Scale deployments based on start and end times.
*   **Customizable schedules:** Define multiple schedules for different times of the day.
*   **Timezone support:** Specify a timezone for each schedule.
*   **Easy to deploy:** Deploy the operator using standard Kubernetes manifests.

## Prerequisites

*   Kubernetes cluster
*   kubectl
*   Helm (optional, for easier deployment)

## Installation

1.  **Deploy the CRD:**

    ```bash
    kubectl apply -f tbsc_crd.yaml
    ```

2.  **Deploy the operator:**

    ```bash
    kubectl apply -f deployment.yaml
    ```

    *Note: Replace `operators` with the desired namespace.*

    *   **Using Helm (Optional):**

        Create a Helm chart for the operator for easier deployment and management.

        ```bash
        helm install time-based-scaling ./helm-chart
        ```

        *Note: Replace `./helm-chart` with the path to your Helm chart.*

## Usage

1.  **Create a TimeBasedScalingController resource:**

    Create a YAML file (e.g., `my-tbsc.yaml`) with the following content:

    ```yaml
    apiVersion: abriment.dev/v1
    kind: TimeBasedScalingController
    metadata:
      name: my-time-based-scaling
      namespace: default  # Replace with the target namespace
    spec:
      defaultReplicas: 2
      schedulingConfig:
        - startTime: "08"
          endTime: "17"
          replicas: 5
          timeZone: "Asia/Tehran"
        - startTime: "18"
          endTime: "23"
          replicas: 3
          timeZone: "Asia/Tehran"
    ```

    *   `defaultReplicas`: The number of replicas to use if no schedule matches the current time.
    *   `schedulingConfig`: An array of scheduling rules.
        *   `startTime`: The start hour (0-23) for scaling.
        *   `endTime`: The end hour (0-23) for scaling.
        *   `replicas`: The number of replicas to scale to.
        *   `timeZone`: The timezone for the schedule (e.g., "America/Los_Angeles", "Etc/UTC"). Defaults to "Etc/UTC".

2.  **Apply the resource:**

    ```bash
    kubectl apply -f my-tbsc.yaml
    ```

3.  **Associate the TBSC with a Deployment:**

    The operator will watch for deployments in the same namespace as the TBSC resource. The operator identifies the deployment to scale by matching the name of the TBSC resource with an annotation on the deployment. Add the following annotation to the deployment's metadata:

    ```yaml
    metadata:
      annotations:
        tbsc.abriment.dev/name: my-time-based-scaling  # Replace with the TBSC resource name
    ```

    *   Replace `my-time-based-scaling` with the name of your `TimeBasedScalingController` resource.

## Configuration

The operator can be configured using environment variables in the deployment.yaml file.

*   `CHECK_INTERVAL`: The interval (in seconds) at which the operator checks the time and scales the deployments. (Default: 60)
