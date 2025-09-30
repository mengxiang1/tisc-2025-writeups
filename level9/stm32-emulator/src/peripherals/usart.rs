// SPDX-License-Identifier: GPL-3.0-or-later

use std::cell::RefCell;
use std::rc::Rc;
use std::io::{self, Read, Write};

use crate::ext_devices::{ExtDevices, ExtDevice};
use crate::system::System;
use super::Peripheral;

#[derive(Default)]
pub struct Usart {
    pub name: String,
    pub ext_device: Option<Rc<RefCell<dyn ExtDevice<(), u8>>>>,
}

impl Usart {
    pub fn new(name: &str, ext_devices: &ExtDevices) -> Option<Box<dyn Peripheral>> {
        if name.starts_with("USART") {
            // Force the ext_device to be stdin/stdout
            Some(Box::new(Self {
                name: name.to_string(),
                ext_device: Some(Rc::new(RefCell::new(StdioDevice {}))),
                ..Default::default()
            }))
        } else {
            None
        }
    }
}

struct StdioDevice;

impl ExtDevice<(), u8> for StdioDevice {
    fn read(&mut self, _sys: &System, _arg: ()) -> u8 {
        let mut buf = [0u8; 1];
        std::io::stdin().read_exact(&mut buf).unwrap_or_default();
        buf[0]
    }

    fn write(&mut self, _sys: &System, _arg: (), value: u8) {
        std::io::stdout().write_all(&[value]).unwrap();
        std::io::stdout().flush().unwrap();
    }

    // Add this method to satisfy the trait
    fn connect_peripheral<'a>(&mut self, peri_name: &str) -> String {
        peri_name.to_string()
    }
}

impl Peripheral for Usart {
    fn read(&mut self, sys: &System, offset: u32) -> u32 {
        match offset {
            0x0000 => {
                // SR register: TXE, TC, RXNE, IDLE all set
                (1 << 7) | (1 << 6) | (1 << 5) | (1 << 4)
            }
            0x0004 => {
                // DR register
                let v = self.ext_device.as_ref().map(|d|
                    d.borrow_mut().read(sys, ())
                ).unwrap_or_default() as u32;

                trace!("{} read={:02x}", self.name, v);
                v
            }
            _ => 0
        }
    }

    fn write(&mut self, sys: &System, offset: u32, value: u32) {
        match offset {
            0x0004 => {
                self.ext_device.as_ref().map(|d|
                    d.borrow_mut().write(sys, (), value as u8)
                );

                trace!("{} write={:02x}", self.name, value as u8);
            }
            _ => {}
        }
    }
}
