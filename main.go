package main

import (
	"fmt"
	"greenmo/gql"
	"greenmo/tools"
)

func main() {
	// res, err := tools.FetchData("reservations.json", httpapi.Data)
	// if err != nil {
	// 	panic(fmt.Errorf("failed to fetch data: %w", err))
	// }

	// err = analytics.Calculate(res)
	// if err != nil {
	// 	panic(fmt.Errorf("failed to calculate interesting facts: %w", err))
	// }

	res, err := tools.FetchData("financials.json", gql.Data)
	if err != nil {
		panic(fmt.Errorf("failed to fetch Gql data: %w", err))
	}
	fmt.Println(res)
}
