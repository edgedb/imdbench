FROM python:3.11 as build
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | sh -s -- -y
RUN curl -sSL https://getsynth.com/install | sh

FROM public.ecr.aws/lambda/python:3.11 as lambda

FROM python:3.11
RUN apt-get update && apt-get install -y postgresql-client && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY --from=build /root/.local /root/.local
COPY --from=build /root/.config /root/.config
COPY --from=lambda /var/runtime /var/runtime
COPY --from=lambda /usr/local/bin/aws-lambda-rie /usr/local/bin/aws-lambda-rie
COPY --from=lambda /lambda-entrypoint.sh /lambda-entrypoint.sh
ENV PATH="/root/.local/bin:${PATH}"
ENV LAMBDA_TASK_ROOT=/var/task
ENV LAMBDA_RUNTIME_DIR=/var/runtime
WORKDIR ${LAMBDA_TASK_ROOT}
COPY requirements-lambda.txt ${LAMBDA_TASK_ROOT}
RUN pip3 install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements-lambda.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip3 install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt
RUN sed -i -e 's/\/var\/lang\//\/usr\/local\//g' /var/runtime/bootstrap*
ENTRYPOINT [ "/lambda-entrypoint.sh" ]
COPY Makefile ${LAMBDA_TASK_ROOT}
COPY dataset ${LAMBDA_TASK_ROOT}/dataset
RUN make new-dataset
COPY . ${LAMBDA_TASK_ROOT}
RUN chmod -R 777 ${LAMBDA_TASK_ROOT} /root
CMD [ "lambda.handler" ]
