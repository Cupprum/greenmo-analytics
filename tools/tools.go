package tools

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
)

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

func FetchData[T any](fileName string, f func() (T, error)) (T, error) {
	var target T

	// Try to open file with data
	err := cachedFile(fileName, &target)
	if err == nil {
		log.Printf("found '%v' in cache, skipping fetching data...\n", fileName)
		return target, nil
	}

	// If file does not exists, fetch data
	log.Printf("'%v' not found in cache, fetchin data...\n", fileName)
	target, err = f()
	if err != nil {
		return target, fmt.Errorf("failed to fetch data: %w", err)
	}

	raw, err := json.Marshal(target)
	if err != nil {
		return target, fmt.Errorf("failed to marshall %v: %w", fileName, err)
	}
	// Store the file in cache for next use
	os.WriteFile(fileName, raw, 0600)

	return target, nil
}

func Req(method, url, token string, query map[string]string, body any, client *http.Client, target any) error {
	var reqBody *bytes.Buffer
	if body != nil {
		jsonData, err := json.Marshal(body)
		if err != nil {
			return fmt.Errorf("failed to marshal JSON: %w", err)
		}
		reqBody = bytes.NewBuffer(jsonData)
	}

	var req *http.Request
	var err error
	// Request creation
	switch method {
	case "GET":
		req, err = http.NewRequest("GET", url, nil)
	case "POST":
		req, err = http.NewRequest("POST", url, reqBody)
	default:
		return fmt.Errorf("unsupported HTTP method: %s", method)
	}
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	if query != nil {
		q := req.URL.Query()
		for k, v := range query {
			q.Add(k, v)
		}
		req.URL.RawQuery = q.Encode()
	}

	if body != nil {
		req.Header.Set("Content-Type", "application/json")

	}

	if client == nil {
		client = http.DefaultClient
	}

	// Request execution
	resp, err := client.Do(req)
	if err != nil || resp.StatusCode != 200 {
		return fmt.Errorf("failed to execute request, response code: %v, error: %w", resp.StatusCode, err)
	}
	defer resp.Body.Close()

	if target != nil {
		// Response parsing
		err = json.NewDecoder(resp.Body).Decode(target)
		if err != nil {
			return fmt.Errorf("failed to decode response: %w", err)
		}
	}
	return nil
}
