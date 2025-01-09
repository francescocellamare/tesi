# Variables
BUCKET_NAME := demo-bucket-cloudformation
STATS_FILE := stats/feedbackLoop.csv
LOCAL_PATH := ./grafana/feedbackLoop.csv

download_stats:
	@echo "Checking for existing stats file..."
	[ -f $(LOCAL_PATH) ] && rm $(LOCAL_PATH) && echo "Removed existing stats file" || echo "Stats file not found"
	@echo "Downloading stats from S3..."
	aws s3 cp s3://$(BUCKET_NAME)/$(STATS_FILE) $(LOCAL_PATH) && echo "Stats downloaded to $(LOCAL_PATH)"

	@echo "Processing stats file..."
	LAST_LINE=$$(tail -n 1 $(LOCAL_PATH)); \
	LAST_ITERATION=$$(echo $$LAST_LINE | cut -d',' -f1); \
	TOTAL_TESTS=$$(echo $$LAST_LINE | cut -d',' -f4); \
	NEW_ITERATION=$$(($$LAST_ITERATION + 1)); \
	NEW_LINE="$$NEW_ITERATION,0,0,$$TOTAL_TESTS"; \
	echo $$NEW_LINE >> $(LOCAL_PATH); \
	echo "Added new row: $$NEW_LINE"

get_dashboard: download_stats
	@echo "Setting up dashboard..."
	mvn verify -q
	mvn test-compile -q org.pitest:pitest-maven:mutationCoverage
	python3 ./script/grafana_setup.py ./target/pit-reports/index.html ./target/pit-reports/output.csv
	docker-compose up
