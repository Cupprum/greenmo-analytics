package analytics

import (
	"fmt"
	"greenmo/gql"
	"greenmo/httpapi"
	"log"
	"sort"
	"time"
)

func minuteDiff(start, end int) (int, error) {
	startTime := time.Unix(int64(start), 0)
	endTime := time.Unix(int64(end), 0)

	duration := endTime.Sub(startTime)
	return int(duration.Minutes()), nil
}

func reservations(res []httpapi.Reservation) error {
	log.Printf("Total reservations: %d\n", len(res))

	payAsYouGoMins := 0
	tripMins := 0
	perYear := map[int]int{}
	uniqueCars := map[string]bool{}

	for _, r := range res {
		if !uniqueCars[r.Plate] {
			uniqueCars[r.Plate] = true
		}

		diff, err := minuteDiff(r.Start, r.End)
		if err != nil {
			return fmt.Errorf("failed to calculate length of trip: %w", err)
		}

		if diff == 0 {
			continue
		}

		year := time.Unix(int64(r.Start), 0).Year()
		if _, ok := perYear[year]; !ok {
			perYear[year] = diff
		} else {
			perYear[year] += diff
		}

		if diff > 120 { // I dont think i ever payed per minutes for more than 2 hours
			tripMins += diff
		} else {
			payAsYouGoMins += diff
		}
	}

	log.Printf("Unique cars: %d\n", len(uniqueCars))
	log.Printf("Minutes driven during trips: %d\n", tripMins)
	log.Printf("Minutes driven paying per minute: %d\n", payAsYouGoMins)

	log.Printf("Minutes driven overall per year:\n")
	keys := make([]int, 0)
	for k, _ := range perYear {
		keys = append(keys, k)
	}
	sort.Ints(keys)
	for _, year := range keys {
		log.Printf("- %d: %d\n", year, perYear[year])
	}

	return nil
}

func financials(fins gql.Financials) error {
	log.Printf("Total Invoices: %d\n", len(fins.Bills))
	log.Printf("Total Vouchers: %d\n", len(fins.Vouchers))

	spent := 0.
	for _, b := range fins.Bills {
		spent += b.Amount
	}

	log.Printf("Total spent: %.2f Dkk\n", spent)

	freeMins := 0.
	boughtMins := 0.
	for _, v := range fins.Vouchers {
		if v.Value > 40 {
			boughtMins += v.Value
		} else {
			freeMins += v.Value
		}
	}

	log.Printf("Total free minutes: %v\n", freeMins)
	log.Printf("Total bought minutes: %v\n", boughtMins)

	return nil
}

func Calculate(httpData []httpapi.Reservation, gqlData gql.Financials) error {
	if err := reservations(httpData); err != nil {
		return fmt.Errorf("failed to calculate data from reservations: %w", err)
	}

	if err := financials(gqlData); err != nil {
		return fmt.Errorf("failed to calculate data from financials: %w", err)
	}

	return nil
}
