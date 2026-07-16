package tcp

import (
	"fmt"
	"net"
)

var Conns chan net.Conn

// create & fill tcp conns to pool
func CreateConnPool(quota int) (bool, error) {
	Conns = make(chan net.Conn, quota)
	var _err error

	for range quota {
		// fill tcp conns
		conn, err := ConnectTCP()
		if err != nil {
			fmt.Println("Tcp connection establishment failed: ", err.Error())
			_err = err
			continue
		}
		Conns <- conn
	}

	if len(Conns) != 0 {
		return true, nil
	} else {
		return false, _err
	}

}

// returns a free tcp conn from pool
func Get_free_conn() net.Conn {
	conn := <-Conns

	return conn
}

// submit tcp conn to pool
func Submit_free_conn(conn net.Conn) bool {
	Conns <- conn

	return true
}
