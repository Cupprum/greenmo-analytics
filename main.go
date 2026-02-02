package main

import (
	"fmt"
	"greenmo/analytics"
	"greenmo/gql"
	"greenmo/httpapi"
	"greenmo/tools"
)

func main() {
	res, err := tools.FetchData[[]httpapi.Reservation]("reservations.json", httpapi.Data)
	if err != nil {
		panic(fmt.Errorf("failed to fetch data: %w", err))
	}

	err = analytics.Calculate(res)
	if err != nil {
		panic(fmt.Errorf("failed to calculate interesting facts: %w", err))
	}

	err = gql.Data()
	if err != nil {
		panic(fmt.Errorf("failed to fetch Gql data: %w", err))
	}
}
