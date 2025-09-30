// Helper to generate token

package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/binary"
	"fmt"
	"math/rand"
)

func genKey(flag []byte) []byte {
	seed := binary.LittleEndian.Uint64(flag[:8])
	src := rand.NewSource(int64(seed))
	for i := 0; i < 256; i++ {
		_ = src.Int63()
	}
	key := make([]byte, 16)
	for j := 0; j < 16; j++ {
		v := src.Int63()
		key[j] = byte(v & 0xff)
	}
	return key
}

func genToken(key, plain []byte) []byte {
	block, _ := aes.NewCipher(key)
	gcm, _ := cipher.NewGCM(block)
	nonce := make([]byte, gcm.NonceSize())
	_, _ = crand.Read(nonce)
	ct := gcm.Seal(nil, nonce, plain, nil)
	token := append(nonce, ct...)
	return token
}

func main() {
	plain := "admin_aaaaaa"
	flag := "TISC{1t_"
	key := genKey([]byte(flag))
	token := genToken(key, []byte(plain))
	fmt.Printf("%x\n", token)
}
