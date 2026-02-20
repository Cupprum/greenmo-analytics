package httpapi

import (
	"fmt"
	"greenmo/tools"
	"log"
	"os"
)

type User struct {
	Id        int    `json:"userId"`
	Reference string `json:"userReference"`
	FirstName string `json:"firstName"`
	LastName  string `json:"lastName"`
	Mail      string `json:"email"`
}

type Reservation struct {
	Plate string `json:"licencePlate"`
	Start int    `json:"openCallSuccessfulTime"`
	End   int    `json:"closeCallSuccessfulTime"`
}

type client struct {
	url   string
	token string
}

func getClient() (client, error) {
	t := os.Getenv("GREENMO_TOKEN")
	if t == "" {
		return client{}, fmt.Errorf("missing env var: `GREENMO_TOKEN`")
	}

	return client{
		url:   "https://greenmobility.frontend.fleetbird.eu/api/prod/v1.06",
		token: t,
	}, nil
}

func (c *client) user() (User, error) {
	var u User

	url := c.url + "/me/"
	err := tools.Req("GET", url, c.token, nil, nil, nil, &u)
	if err != nil {
		return u, fmt.Errorf("failed to get userid: %w", err)
	}
	log.Printf("User ID: %d\n", u.Id)

	return u, nil
}

func (c *client) reservations(uid int) ([]Reservation, error) {
	pageId := 1 // If this is set to 0, the API returns everything at the same time
	reservations := []Reservation{}

	for {
		res := []Reservation{}

		url := fmt.Sprintf("%v/users/%d/reservations/pages/%d/?orderBy=desc", c.url, uid, pageId)
		err := tools.Req("GET", url, c.token, nil, nil, nil, &res)
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

func GetUser() (User, error) {
	c, err := getClient()
	if err != nil {
		return User{}, fmt.Errorf("failed to create client: %w", err)
	}

	u, err := c.user()
	if err != nil {
		return u, fmt.Errorf("failed to get details about user: %w", err)
	}

	return u, nil
}

func Data() ([]Reservation, error) {
	c, err := getClient()
	if err != nil {
		return nil, fmt.Errorf("failed to create client: %w", err)
	}

	user, err := c.user()
	if err != nil {
		return nil, fmt.Errorf("failed to get details about user: %w", err)
	}

	res, err := c.reservations(user.Id)
	if err != nil {
		return nil, fmt.Errorf("failed to get reservations: %w", err)
	}

	return res, nil
}
