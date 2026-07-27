package common

import (
	"crypto/hmac"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"strconv"
	"strings"
	"time"
)

func VerifyHMACSHA256(body []byte, secret, provided, prefix string) bool {
	actual := strings.TrimPrefix(provided, prefix)
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	expected := base64.StdEncoding.EncodeToString(mac.Sum(nil))
	if len(expected) != len(actual) {
		return false
	}
	return subtle.ConstantTimeCompare([]byte(expected), []byte(actual)) == 1
}
func VerifyHMACSHA256Hex(body []byte, secret, provided, prefix string) bool {
	actual := strings.TrimPrefix(provided, prefix)
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	expected := hex.EncodeToString(mac.Sum(nil))
	if len(expected) != len(actual) {
		return false
	}
	return subtle.ConstantTimeCompare([]byte(expected), []byte(actual)) == 1
}
func VerifySlackSignature(body []byte, secret, timestamp, provided string) bool {
	value, err := strconv.ParseInt(timestamp, 10, 64)
	if err != nil || absInt64(time.Now().Unix()-value) > 300 {
		return false
	}
	return VerifyHMACSHA256Hex([]byte("v0:"+timestamp+":"+string(body)), secret, provided, "v0=")
}
func absInt64(value int64) int64 {
	if value < 0 {
		return -value
	}
	return value
}
