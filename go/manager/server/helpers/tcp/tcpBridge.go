package tcp

import (
	"encoding/binary"
	"io"
	"net"
)

// TCP Helpers

// const addr string = "localhost:9090"

var UnixAddr = ""

// debug
// const addr string = "192.168.1.2:9090"
const CHUNK = 64 * 1024

// Utils
func Min(a int64, b int64) int64 {
	var min_value int64
	if a > b {
		min_value = b
	} else {
		min_value = a
	}
	return min_value
}

// send_msg
func SendMsg(conn net.Conn, data []byte) error {
	length := uint32(len(data))
	buf := make([]byte, 4)
	binary.BigEndian.PutUint32(buf, length)

	_, err := conn.Write(append(buf, data...))
	return err
}

// recv_exact
func RecvExact(conn net.Conn, n int) ([]byte, error) {
	buf := make([]byte, n)
	_, err := io.ReadFull(conn, buf)
	return buf, err
}

// recv_msg
func RecvMsg(conn net.Conn) ([]byte, error) {
	lenBytes, err := RecvExact(conn, 4)
	if err != nil {
		return nil, err
	}

	length := binary.BigEndian.Uint32(lenBytes)
	return RecvExact(conn, int(length))
}

func ConnectTCP() (net.Conn, error) {
	// return net.Dial("tcp", addr)
	return net.Dial("unix", UnixAddr)
}
