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

type GqlClient struct {
	url    string
	client *http.Client
	token  string
}

func (c *GqlClient) getToken() (string, error) {
	u, err := url.Parse(c.url + "/go/drive/account")
	if err != nil {
		return "", fmt.Errorf("failed to parse URL: %w", err)
	}

	for _, cookie := range c.client.Jar.Cookies(u) {
		if cookie.Name == "driveToken" {
			return cookie.Value, nil
		}
	}
	return "", fmt.Errorf("missing `driveToken` cookie")
}

func gqlClient(user httpapi.User) (GqlClient, error) {
	var c GqlClient
	c.url = "https://street.greenmobility.com/api"

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
	err = tools.Req("GET", c.url+"/go/drive/account", "", params, nil, c.client, nil)
	if err != nil {
		return c, fmt.Errorf("failed to execute request: %w", err)
	}

	// Verify the cookie
	c.token, err = c.getToken()
	if err != nil {
		return c, fmt.Errorf("failed to find token: %w", err)
	}

	return c, nil
}

type Invoice struct {
	Date  time.Time `json:"date"`
	Total struct {
		Amount float64 `json:"amount"`
	} `json:"total"`
}

type Voucher struct {
	Value     float64   `json:"value"`
	GrantedAt time.Time `json:"grantedAt"`
}

type GraphQLResponse struct {
	Data struct {
		Viewer struct {
			Invoices       []Invoice `json:"invoices"`
			CreditVouchers struct {
				Edges []struct {
					Node Voucher `json:"node"`
				} `json:"edges"`
			} `json:"creditVouchers"`
		} `json:"viewer"`
	} `json:"data"`
}

type Bill struct {
	Date   time.Time `json:"date"`
	Amount float64   `json:"amount"`
}

func (c *GqlClient) getBills() ([]Bill, error) {
	b := map[string]interface{}{
		"variables": map[string]interface{}{
			"offset": 0,
			"limit":  10,
		},
		"query": `query GetInvoices($limit: Int!, $offset: Int, $invoiceStatus: InvoiceStatus) {
			viewer {
				invoices(limit: $limit, offset: $offset, invoiceStatus: $invoiceStatus) {
					date
					total {
						amount
					}
				}
			}
		}`,
	}

	bills := []Bill{}

	for {
		resp := GraphQLResponse{}
		err := tools.Req("POST", c.url+"/drive/graphql", c.token, nil, b, c.client, &resp)
		if err != nil {
			return nil, fmt.Errorf("failed to execute request: %w", err)
		}

		if len(resp.Data.Viewer.Invoices) == 0 {
			break
		}
		for _, i := range resp.Data.Viewer.Invoices {
			bill := Bill{
				Date:   i.Date,
				Amount: i.Total.Amount / 100,
			}
			bills = append(bills, bill)
		}

		// Update the offset for the next batch
		b["variables"].(map[string]interface{})["offset"] = 10 + b["variables"].(map[string]interface{})["offset"].(int)
	}

	return bills, nil
}

func (c *GqlClient) getVouchers() ([]Voucher, error) {
	b := map[string]interface{}{
		"variables": map[string]interface{}{
			"offset": 0,
			"limit":  20,
		},
		"query": `query getCreditVouchers($limit: Int!, $offset: Int!) {
			viewer {
				creditVouchers(limit: $limit, offset: $offset) {
					edges {
						node {
						id
						value
						grantedAt
						}
					}
				}
			}
		}`,
	}

	vouchers := []Voucher{}

	for {
		resp := GraphQLResponse{}
		err := tools.Req("POST", c.url+"/drive/graphql", c.token, nil, b, c.client, &resp)
		if err != nil {
			return nil, fmt.Errorf("failed to execute request: %w", err)
		}

		if len(resp.Data.Viewer.CreditVouchers.Edges) == 0 {
			break
		}
		for _, e := range resp.Data.Viewer.CreditVouchers.Edges {
			vouchers = append(vouchers, e.Node)
			fmt.Println(e.Node)
		}

		// Update the offset for the next batch
		b["variables"].(map[string]interface{})["offset"] = 1 + b["variables"].(map[string]interface{})["offset"].(int)
	}

	return vouchers, nil
}

type Financials struct {
	Bills    []Bill    `json:"bills"`
	Vouchers []Voucher `json:"vouchers"`
}

func Data() (Financials, error) {
	f := Financials{}

	u, err := httpapi.GetUser()
	if err != nil {
		return f, fmt.Errorf("failed to get user details: %w", err)
	}

	c, err := gqlClient(u)
	if err != nil {
		return f, fmt.Errorf("failed to create Gql client: %w", err)
	}

	bills, err := c.getBills()
	if err != nil {
		return f, fmt.Errorf("failed to get bills: %w", err)
	}

	vouchers, err := c.getVouchers()
	if err != nil {
		return f, fmt.Errorf("failed to get vouchers: %w", err)
	}

	f.Bills = bills
	f.Vouchers = vouchers

	return f, nil
}
