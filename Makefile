.PHONY: get-data clean-data

get-data:
	pipeline/get_data.sh

clean-data:
	rm -rf data/raw data/subsets data/merged
