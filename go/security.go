package common

import("crypto/hmac";"crypto/sha256";"crypto/subtle";"encoding/base64";"encoding/hex";"strings")
func VerifyHMACSHA256(body []byte, secret, provided, prefix string) bool { actual:=strings.TrimPrefix(provided,prefix);mac:=hmac.New(sha256.New,[]byte(secret));mac.Write(body);expected:=base64.StdEncoding.EncodeToString(mac.Sum(nil));if len(expected)!=len(actual){return false};return subtle.ConstantTimeCompare([]byte(expected),[]byte(actual))==1 }
func VerifyHMACSHA256Hex(body []byte, secret, provided, prefix string) bool { actual:=strings.TrimPrefix(provided,prefix);mac:=hmac.New(sha256.New,[]byte(secret));mac.Write(body);expected:=hex.EncodeToString(mac.Sum(nil));if len(expected)!=len(actual){return false};return subtle.ConstantTimeCompare([]byte(expected),[]byte(actual))==1 }
func VerifySlackSignature(body []byte, secret, timestamp, provided string) bool { return VerifyHMACSHA256Hex([]byte("v0:"+timestamp+":"+string(body)),secret,provided,"v0=") }
