# Person Detector Service

This service detects person in images, providing these detections in different ways.

## About :smile:

> YOLOv8 was released by Ultralytics on January 10th, 2023, offering cutting-edge performance in terms of accuracy and speed. Building upon the advancements of previous YOLO versions, YOLOv8 introduced new features and optimizations that make it an ideal choice for various object detection tasks in a wide range of applications. [See more](https://docs.ultralytics.com/models/yolov8/)


## Streams :camera:

A stream is a program that consumes messages with a specific topic, processes them, and publishes messages in other topics, so if another service wants to use the informations provided by this service, it can simply subscribe to receive messages with the topic of interest. The python script responsible for the stream in the table below can be found in [`src/is_person_detector/stream.py`](https://github.com/JoabFelippx/is-person-detector/blob/main/is_person_detector/stream.py).

| Name | ⇒ Input | Output  ⇒ | Description |
| ---- | ------- | --------- | ----------- |
| Person.Detection | :incoming_envelope: **topic:** `CameraGateway.(camera_id).Frame` <br> :gem: **schema:** [Image] | :incoming_envelope: **topic:**  `PersonDetector.(camera_id).Detection` <br> :gem: **schema:** [ObjectAnnotations] | Detects person on images published by cameras and publishes an ObjectAnnotations message containing all the detected persons. |
| Person.Detection | :incoming_envelope: **topic:** `CameraGateway.(camera_id).Frame` <br> :gem: **schema:** [Image]| :incoming_envelope: **topic:** `PersonDetector.(camera_id).Rendered` <br> :gem: **schema:** [Image]| After detection, persons are drew on input image and published for visualization.|

## Configuration :gear:

Configuration file can be found in [`etc/conf/options.json`](https://github.com/JoabFelippx/is-person-detector/blob/main/etc/conf/options.json).

## Developing :hammer_and_wrench:

The project structure follows as:

```bash
.
├── etc
│   ├── conf
│   │   └── options.json
│   └── docker
│       └── Dockerfile
├── is_person_detector
│   ├── detector.py
│   ├── stream.py
│   ├── stream_channel.py
│   └── utils.py
├── model
│   └── utils.py
├── README.md
└── requirements.txt
```

* [`etc/conf/options.json`](https://github.com/JoabFelippx/is-person-detector/blob/main/etc/conf/options.json): Example of JSON configuration file. Also used as default if none is passed;

* [`etc/docker/Dockerfile`](https://github.com/JoabFelippx/is-person-detector/blob/main/etc/docker/Dockerfile): Dockerfile with the instructions to build a docker image with this application;

* [`is_person_detector`](https://github.com/JoabFelippx/is-person-detector/tree/main/is_person_detector): python module with all the scripts;

* [`is_person_detector/stream.py`](https://github.com/JoabFelippx/is-person-detector/blob/main/is_person_detector/stream.py): main python script for a Stream behavior;

### is-wire-py :incoming_envelope:

For a service to communicate with another, it uses a message-based protocol ([AMQP](https://github.com/celery/py-amqp)) which depends of a broker to receive and deliver all messages ([RabbitMQ](https://www.rabbitmq.com/)).

A python package was developed to abstract the communication layer implementing a publish/subscribe middleware, know as [is-wire-py](https://github.com/labvisio/is-wire-py). There you can find basic examples of message sending and receiving, or creating an RPC server, tracing messages, etc.

### Docker <img alt="docker" width="26px" src="https://raw.githubusercontent.com/github/explore/80688e429a7d4ef2fca1e82350fe8e3517d3494d/topics/docker/docker.png" />

To run the application into kubernetes platform, it must be packaged in the right format which is a [docker container](https://www.docker.com/resources/what-container). A docker container can be initialized from a docker image, the instructions to build the docker image are at [`etc/docker/Dockerfile`](https://github.com/JoabFelippx/is-person-detector/blob/main/etc/docker/Dockerfile).

To be available to the kubernetes cluster, the docker image must be stored on [dockerhub](https://hub.docker.com/), to build the image locally and push to dockerhub:

```bash
docker build -f etc/docker/Dockerfile -t <user>/is-person-detector:<version> .
docker push <user>/is-person-detector:<version>
```
