// Helper to brute force main_key seed

package main

import (
	"crypto/aes"
	"crypto/cipher"
	"encoding/binary"
	"encoding/hex"
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

func decrypt(key, token []byte) ([]byte, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	nonceSize := gcm.NonceSize()
	if len(token) < nonceSize {
		return nil, fmt.Errorf("token too short")
	}
	nonce := token[:nonceSize]
	ct := token[nonceSize:]
	plain, err := gcm.Open(nil, nonce, ct, nil)
	if err != nil {
		return nil, err
	}
	return plain, nil
}

func main() {
	known := "TISC{"
	tokenHex := "c89889133788148b71b4ea6dd352afebcc5f5afddb35615b28dcb345cd418eb38112"
	token, _ := hex.DecodeString(tokenHex)

	chars := "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

	for i := 0; i < len(chars); i++ {
		for j := 0; j < len(chars); j++ {
			for k := 0; k < len(chars); k++ {
				candidate := known + string([]byte{chars[i], chars[j], chars[k]})
				key := genKey([]byte(candidate))
				plain, err := decrypt(key, token)
				if err == nil {
					fmt.Printf("Candidate: %s\n", candidate)
					fmt.Printf("Plaintext: %s\n", string(plain))
				}
			}
		}
	}
}
