package common

import("crypto/hmac";"crypto/sha256";"crypto/subtle";"encoding/base64";"strings")
func VerifyHMACSHA256(body []byte, secret, provided, prefix string) bool { actual:=strings.TrimPrefix(provided,prefix);mac:=hmac.New(sha256.New,[]byte(secret));mac.Write(body);expected:=base64.StdEncoding.EncodeToString(mac.Sum(nil));if len(expected)!=len(actual){return false};return subtle.ConstantTimeCompare([]byte(expected),[]byte(actual))==1 }
