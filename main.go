package main

import (
	"fmt"
	"greenmo/analytics"
	"greenmo/gql"
	"greenmo/httpapi"
	"greenmo/tools"
)

func main() {
	res, err := tools.FetchData("reservations.json", httpapi.Data)
	if err != nil {
		panic(fmt.Errorf("failed to fetch data: %w", err))
	}

	fins, err := tools.FetchData("financials.json", gql.Data)
	if err != nil {
		panic(fmt.Errorf("failed to fetch Gql data: %w", err))
	}

	err = analytics.Calculate(res, fins)
	if err != nil {
		panic(fmt.Errorf("failed to calculate interesting facts: %w", err))
	}
}
