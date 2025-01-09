BUCKET_NAME := demo-bucket-cloudformation
PACKAGE_BUCKET := demo-bucket-cloudformation
LOCAL_PATH := ~/tesi/AWS/s3
TEMPLATE_FILE := ~/tesi/AWS/Prototype/my_template.yml
PACKAGED_TEMPLATE := ~/tesi/AWS/Prototype/packaged_template.yml
REGION := eu-south-1
STACK_NAME ?= MyCloudFormationStack
path ?= ./demo

downloadS3:
	rm -rf $(LOCAL_PATH)/*
	aws s3 cp s3://$(BUCKET_NAME) $(LOCAL_PATH)/ --recursive
	echo "Bucket $(BUCKET_NAME) downloaded"

cleanS3:
	aws s3 rm --recursive s3://${BUCKET_NAME}/DemoPipeline/
	echo "Bucket $(BUCKET_NAME) clean"

deleteS3:
	aws s3 rm s3://$(BUCKET_NAME) --recursive
	aws s3api delete-bucket --bucket $(BUCKET_NAME) --region $(REGION)
	echo "Bucket $(BUCKET_NAME) deleted"

create_template:
	aws cloudformation package --template-file $(TEMPLATE_FILE) \
		--s3-bucket $(PACKAGE_BUCKET) \
		--s3-prefix lambdacode \
		--output-template-file $(PACKAGED_TEMPLATE)
	echo "Template created"

deploy_template:
	@if [ "$(STACK_NAME)" = "" ]; then \
	  echo "Error: STACK_NAME is required. Use 'make deploy_template STACK_NAME=<name>'"; \
	  exit 1; \
	fi
	aws s3 cp $(PACKAGED_TEMPLATE) s3://$(BUCKET_NAME)/packaged_template.yml --region $(REGION)
	aws cloudformation deploy \
		--template-url https://$(BUCKET_NAME).s3.$(REGION).amazonaws.com/packaged_template.yml \
		--stack-name $(STACK_NAME) \
		--region $(REGION) \
		--capabilities CAPABILITY_NAMED_IAM
	echo "Stack $(STACK_NAME) deployed successfully"

delete_stack:
	@if [ "$(STACK_NAME)" = "" ]; then \
	  echo "Error: STACK_NAME is required. Use 'make delete_stack STACK_NAME=<name>'"; \
	  exit 1; \
	fi
	$(MAKE) deleteS3
	aws cloudformation delete-stack \
		--stack-name $(STACK_NAME) \
		--region $(REGION)
	echo "Stack $(STACK_NAME) deletion initiated"

update_stack:
	@if [ "$(STACK_NAME)" = "" ]; then \
	  echo "Error: STACK_NAME is required. Use 'make update_stack STACK_NAME=<name>'"; \
	  exit 1; \
	fi
	aws s3 cp $(PACKAGED_TEMPLATE) s3://$(BUCKET_NAME)/packaged_template.yml --region $(REGION)
	aws cloudformation update-stack \
		--stack-name $(STACK_NAME) \
		--template-url https://$(BUCKET_NAME).s3.$(REGION).amazonaws.com/packaged_template.yml \
		--region $(REGION) \
		--capabilities CAPABILITY_NAMED_IAM
	echo "Stack $(STACK_NAME) updated successfully"

.PHONY: setup_pipeline
.SILENT: setup_pipeline
setup_pipeline:
	echo "Setting up the pipeline at $(path)"
	echo "Moving things around..."
	cp -r ./resources/* $(path)
	echo "Done"
	echo "Choose which directory you want to test"
	python3 $(path)/script/select_path.py
	echo "Done"
