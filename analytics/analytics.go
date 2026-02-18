package analytics

import (
	"fmt"
	"greenmo/httpapi"
	"log"
	"time"
)

func minuteDiff(start, end int) (int, error) {
	startTime := time.Unix(int64(start), 0)
	endTime := time.Unix(int64(end), 0)

	duration := endTime.Sub(startTime)
	return int(duration.Minutes()), nil
}

func Calculate(res []httpapi.Reservation) error {
	log.Printf("Total reservations: %d\n", len(res))

	totalMins := 0
	uniqueCars := map[string]bool{}

	for _, r := range res {
		if !uniqueCars[r.Plate] {
			uniqueCars[r.Plate] = true
		}

		diff, err := minuteDiff(r.Start, r.End)
		if err != nil {
			return fmt.Errorf("failed to calculate length of trip: %w", err)
		}
		totalMins += diff
	}

	log.Printf("Minutes driven: %d\n", totalMins)
	log.Printf("Unique cars: %d\n", len(uniqueCars))

	return nil
}
