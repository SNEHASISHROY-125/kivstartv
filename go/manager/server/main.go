package main

import (
	"embed"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"sync"

	. "org.snehasys.linux/helpers/download"
	. "org.snehasys.linux/helpers/tcp"
)

//go:embed src/*
var webfiles embed.FS

var manager_db sync.Map

func root(w http.ResponseWriter, r *http.Request) {
	// serve static html
	index, err := webfiles.ReadFile("src/index.html")
	fmt.Println(len(index))

	if err != nil {
		http.Error(w, "internal error", 500)
	}

	w.Header().Set("Content-Type", "text/html")
	w.Write(index)
}

func icondownloader(w http.ResponseWriter, r *http.Request) {
	url := r.URL.Query().Get("q")
	url, err := GetCachedFile(url)

	if err == nil {
		fmt.Println("recived to downlod: ", url)

		// w.Write([]byte("ok"))
		// http.ServeFile(w, r, url)
		file, err := os.Open(url)
		if err != nil {
			http.Error(w, err.Error(), 500)
		}
		defer file.Close()

		r.Header.Set("Content-Type", "image/jpeg")
		io.Copy(w, file)

	} else {
		fmt.Println("err: ", err.Error())

		w.Write([]byte("error" + err.Error()))
	}
}

/* ------- CORS ---------- */
func enableCORS(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
}
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		enableCORS(w)

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func main() {

	http.HandleFunc("/channels", root)
	http.HandleFunc("/download", icondownloader)

	// setup
	Cache = "/home/roy/.local/share/KivstarTV/archive/cache"
	UnixAddr = ""

	host := "0.0.0.0"
	port := strconv.Itoa(8030)

	addr := host + ":" + port
	err := http.ListenAndServe(addr, nil)
	if err != nil {
		log.Fatal(err)
	}
}
