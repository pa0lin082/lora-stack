#!/bin/sh
mkdir -p meshtasticMqttToInfluxDb/generated
pipenv run python -m grpc_tools.protoc -Iprotobufs --python_out=meshtasticMqttToInfluxDb/generated --pyi_out=meshtasticMqttToInfluxDb/generated --grpc_python_out=meshtasticMqttToInfluxDb/generated protobufs/*.proto protobufs/meshtastic/*.proto