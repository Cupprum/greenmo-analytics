package gql

import (
	"fmt"
	"greenmo/httpapi"
	"greenmo/tools"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strconv"
	"time"
)

// curl -v -L 'https://street.greenmobility.com/api/go/drive/account?customerReference=KHZTUKFYE8&customerId=175079&firstName=Samuel&lastName=Branisa&email=branisa.samuel%40icloud.com'

type GqlClient struct {
	url    string
	client *http.Client
}

func gqlClient(user httpapi.User) (GqlClient, error) {
	var c GqlClient
	c.url = "https://street.greenmobility.com/api/go/drive"

	// Create a cookie jar for persisting cookies across requests
	jar, err := cookiejar.New(nil)
	if err != nil {
		return c, fmt.Errorf("failed to create cookie jar: %w", err)
	}

	c.client = &http.Client{
		Jar:     jar,
		Timeout: 30 * time.Second,
	}

	params := map[string]string{
		"customerReference": user.Reference,
		"customerId":        strconv.Itoa(user.Id),
		"firstName":         user.FirstName,
		"lastName":          user.LastName,
		"email":             user.Mail,
	}

	// Set the cookie
	err = tools.Req(c.url+"/account", "", params, c.client, nil)
	if err != nil {
		return c, fmt.Errorf("failed to execute request: %w", err)
	}

	// Verify the cookie
	u, err := url.Parse(c.url + "/account")
	if err != nil {
		return c, fmt.Errorf("failed to parse URL: %w", err)
	}
	for _, cookie := range c.client.Jar.Cookies(u) {
		if cookie.Name == "driveToken" {
			return c, nil
		}
	}

	return c, fmt.Errorf("missing `driveToken` cookie")
}

type Invoice struct {
	Amount int
}

func getInvoices() error {

	return nil
}

func Data() error {
	u, err := httpapi.GetUser()
	if err != nil {
		return fmt.Errorf("failed to get user details: %w", err)
	}

	_, err = gqlClient(u)
	if err != nil {
		return fmt.Errorf("failed to create Gql client: %w", err)
	}

	return nil
}
