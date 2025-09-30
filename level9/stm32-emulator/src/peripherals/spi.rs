// SPDX-License-Identifier: GPL-3.0-or-later

use crate::{system::System, ext_devices::ExtDevice};
use super::Peripheral;

use crate::ext_devices::ExtDevices;

use std::{rc::Rc, cell::RefCell};

#[derive(Default)]
pub struct Spi {
    pub name: String,
    pub cr1: u32,
    /// holds one received value (for 8-bit) or combined 16-bit (for 16-bit mode)
    pub rx_buffer: u32,
    /// indicates whether rx_buffer contains unread data (i.e. RXNE should be set)
    pub rx_have: bool,
    /// indicates whether transmit buffer is empty (TXE)
    pub tx_empty: bool,
    pub ext_device: Option<Rc<RefCell<dyn ExtDevice<(), u8>>>>,
}

impl Spi {
    pub fn new(name: &str, ext_devices: &ExtDevices) -> Option<Box<dyn Peripheral>> {
        if name.starts_with("SPI") {
            // Keep the same device lookup as the original code (find_serial_device)
            // If your ExtDevices has find_spi_device, you can change to that.
            let ext_device = ext_devices.find_serial_device(name);
            let name = ext_device.as_ref()
                .map(|d| d.borrow_mut().connect_peripheral(name))
                .unwrap_or_else(|| name.to_string());

            Some(Box::new(Self {
                name,
                ext_device,
                cr1: 0,
                rx_buffer: 0,
                rx_have: false,
                tx_empty: true,
            }))
        } else {
            None
        }
    }

    pub fn is_16bits(&self) -> bool {
        self.cr1 & (1 << 11) != 0
    }
}

impl Peripheral for Spi {
    fn read(&mut self, sys: &System, offset: u32) -> u32 {
        match offset {
            0x0000 => {
                // CR1
                self.cr1
            }
            0x0008 => {
                // SR register: bit0 RXNE, bit1 TXE
                let mut sr = 0u32;
                if self.rx_have {
                    sr |= 1; // RXNE
                }
                if self.tx_empty {
                    sr |= 1 << 1; // TXE
                }
                // NOTE: do not toggle this value artificially; let rx_have/tx_empty decide
                trace!("read: addr=? peri={} offset=SR read=0x{:08x}", self.name, sr);
                sr
            }
            0x000C => {
                // DR register: MCU reads received byte(s)
                let v = self.rx_buffer;
                if self.is_16bits() {
                    trace!("{} read DR (16-bit) = 0x{:04x}", self.name, v as u16);
                } else {
                    trace!("{} read DR (8-bit) = 0x{:02x}", self.name, v as u8);
                }
                // reading DR clears RXNE (we've consumed the data)
                self.rx_have = false;
                // After read, return the stored value
                v
            }
            _ => {
                trace!("read: addr=? peri={} offset=0x{:x} unknown read=0", self.name, offset);
                0
            }
        }
    }

    fn write(&mut self, sys: &System, offset: u32, value: u32) {
        match offset {
            0x0000 => {
                // CR1 register write
                self.cr1 = value;
                trace!("write: peri={} offset=CR1 write=0x{:08x}", self.name, value);
            }
            0x000C => {
                // DR register write: MCU writes MOSI bytes -> forward to device, then fetch MISO
                if self.is_16bits() {
                    // 16-bit mode: firmware writes 16-bit in one write; break into two bytes
                    let hi = ((value >> 8) & 0xFF) as u8;
                    let lo = (value & 0xFF) as u8;
                    trace!("{} write DR (16-bit) write hi=0x{:02x} lo=0x{:02x}", self.name, hi, lo);

                    if let Some(ref d) = self.ext_device {
                        // forward hi then lo to device as the MOSI stream
                        d.borrow_mut().write(sys, (), hi);
                        d.borrow_mut().write(sys, (), lo);

                        // attempt to read two response bytes synchronously (typical SPI behavior)
                        let rhi = d.borrow_mut().read(sys, ());
                        let rlo = d.borrow_mut().read(sys, ());
                        self.rx_buffer = ((rhi as u32) << 8) | (rlo as u32);
                        self.rx_have = true;
                        trace!("{} ext_device responded rhi=0x{:02x} rlo=0x{:02x}", self.name, rhi, rlo);
                    } else {
                        // no ext device: echo bytes back
                        self.rx_buffer = ((hi as u32) << 8) | (lo as u32);
                        self.rx_have = true;
                        trace!("{} no ext_device: echo 16-bit {:04x}", self.name, self.rx_buffer);
                    }

                    // After writing, TX buffer becomes empty
                    self.tx_empty = true;
                } else {
                    // 8-bit mode
                    let b = (value & 0xFF) as u8;
                    trace!("{} write DR (8-bit) write 0x{:02x}", self.name, b);

                    if let Some(ref d) = self.ext_device {
                        // forward MOSI byte
                        d.borrow_mut().write(sys, (), b);
                        trace!("{} ext_device.write({:02x}) forwarded", self.name, b);
                        // immediately read MISO byte in response
                        let resp = d.borrow_mut().read(sys, ());
                        self.rx_buffer = resp as u32;
                        self.rx_have = true;
                        trace!("{} ext_device.read() -> {:02x} (stored in rx_buffer)", self.name, resp);
                    } else {
                        // no ext device -> echo back
                        self.rx_buffer = b as u32;
                        self.rx_have = true;
                        trace!("{} no ext_device: echo 0x{:02x}", self.name, b);
                    }

                    // After writing, TX buffer becomes empty
                    self.tx_empty = true;
                }
            }
            _ => {
                trace!("write: peri={} offset=0x{:x} unknown write=0x{:08x}", self.name, offset, value);
            }
        }
    }
}
