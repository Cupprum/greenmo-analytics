package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

type Client struct {
	url   string
	token string
}

func client() (Client, error) {
	t := os.Getenv("GREENMO_TOKEN")
	if t == "" {
		return Client{}, fmt.Errorf("missing env var: `GREENMO_TOKEN`")
	}

	return Client{
		url:   "https://greenmobility.frontend.fleetbird.eu/api/prod/v1.06",
		token: t,
	}, nil
}

func (c *Client) req(path string, target any) error {
	// Request creation
	url := c.url + path
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+c.token)

	// Request execution
	resp, err := http.DefaultClient.Do(req)
	if err != nil || resp.StatusCode != 200 {
		return fmt.Errorf("failed to execute request, response code: %v, error: %w", resp.StatusCode, err)
	}
	defer resp.Body.Close()

	// Response parsing
	err = json.NewDecoder(resp.Body).Decode(target)
	if err != nil {
		return fmt.Errorf("failed to decode response: %w", err)
	}
	return nil
}

type reservation struct {
	Plate string `json:"licencePlate"`
	Start int    `json:"startTime"`
	End   int    `json:"endTime"`
}

func (c *Client) reservations(uid int) ([]reservation, error) {
	pageId := 0
	reservations := []reservation{}

	for {
		res := []reservation{}

		path := fmt.Sprintf("/users/%d/reservations/pages/%d/?orderBy=desc", uid, pageId)
		err := c.req(path, &res)
		if err != nil {
			return nil, fmt.Errorf("failed to get reservations: %w", err)
		}

		if len(res) == 0 {
			break
		}

		reservations = append(reservations, res...)
		pageId++
	}

	return reservations, nil
}

func cachedFile(name string, target any) error {
	f, err := os.ReadFile(name)
	if err != nil {
		return fmt.Errorf("failed to read `%v` file: %w", name, err)
	}

	if err := json.Unmarshal(f, &target); err != nil {
		return fmt.Errorf("failed to parse the `%v` file: %w", name, err)
	}

	return nil
}

func fetchData() ([]reservation, error) {
	fileName := "reservations.json"

	// Try to open file with data
	var res []reservation
	err := cachedFile(fileName, &res)
	if err == nil {
		log.Println("found reservations in cache, skipping fetching data...")
		return res, nil
	}

	log.Println("reservations not found in cache, fetchin data...")
	// If file does not exists, fetch data
	c, err := client()
	if err != nil {
		return nil, fmt.Errorf("failed to create client: %w", err)
	}

	var me struct {
		ID int `json:"userId"`
	}
	err = c.req("/me/", &me)
	if err != nil {
		return nil, fmt.Errorf("failed to get userid: %w", err)
	}
	log.Printf("User ID: %d\n", me.ID)

	res, err = c.reservations(me.ID)
	if err != nil {
		return nil, fmt.Errorf("failed to get reservations: %w", err)
	}

	raw, err := json.Marshal(res)
	if err != nil {
		return nil, fmt.Errorf("failed to marshall reservations: %w", err)
	}
	// Store the file in cache for next use
	os.WriteFile(fileName, raw, 0600)

	return res, nil
}

func minuteDiff(start, end int) (int, error) {
	startTime := time.Unix(int64(start), 0)
	endTime := time.Unix(int64(end), 0)

	duration := endTime.Sub(startTime)
	return int(duration.Minutes()), nil
}

func calculate(res []reservation) error {
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

func main() {
	res, err := fetchData()
	if err != nil {
		panic(fmt.Errorf("failed to fetch data: %w", err))
	}

	err = calculate(res)
	if err != nil {
		panic(fmt.Errorf("failed to calculate interesting facts: %w", err))
	}
}
