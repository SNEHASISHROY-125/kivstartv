package helpers

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"net/http"
	"os"
	"path"
)

var Cache string

func cacheFileName(url string) string {
	hash := sha256.Sum256([]byte(url))
	name := hex.EncodeToString(hash[:])

	// Preserve extension if possible
	// u, _ := url.Parse(url)
	ext := path.Ext(url)
	if ext == "" {
		ext = ".jpeg"
	}

	return Cache + "/" + name + ext
}

func GetCachedFile(url string) (string, error) {
	filename := cacheFileName(url)

	// Already cached?
	if _, err := os.Stat(filename); err == nil {
		fmt.Println("Cache hit:", filename)
		return filename, nil
	}

	fmt.Println("Downloading:", url)

	resp, err := http.Get(url)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("HTTP %d", resp.StatusCode)
	}

	// Ensure cache directory exists
	if err := os.MkdirAll("./cache", 0755); err != nil {
		return "", err
	}

	file, err := os.Create(filename)
	if err != nil {
		return "", err
	}
	defer file.Close()

	if _, err := io.Copy(file, resp.Body); err != nil {
		return "", err
	}

	return filename, nil
}
