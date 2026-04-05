# Baseline Coverage Summary

| DUT | Status | Line % | Branch % |
|-----|--------|--------|----------|
| nexus_uart | ok | 60.08 | 14.49 |
| bastion_gpio | ok | 73.21 | 13.77 |
| warden_timer | ok | 71.28 | 20.66 |
| citadel_spi | ok | 57.17 | 22.08 |
| aegis_aes | ok | 34.33 | 8.11 |
| sentinel_hmac | ok | 47.49 | 6.58 |
| rampart_i2c | ok | 49.33 | 23.49 |

## Top Uncovered Regions (per DUT)

### nexus_uart
- duts/nexus_uart/nexus_uart.sv | uncovered=188 | ranges=523-533, 587-595, 110-116, 92-97, 401-406, 545-550, 61-65, 422-426

### bastion_gpio
- duts/bastion_gpio/bastion_gpio.sv | uncovered=56 | ranges=42-48, 57-61, 18-21, 217-220, 224-227, 50-52, 23-24, 54-55

### warden_timer
- duts/warden_timer/warden_timer.sv | uncovered=83 | ranges=56-65, 49-54, 293-297, 69-72, 92-95, 250-253, 257-260, 316-319

### citadel_spi
- duts/citadel_spi/citadel_spi.sv | uncovered=263 | ranges=126-141, 105-114, 757-765, 96-103, 452-459, 773-780, 788-795, 659-664

### aegis_aes
- duts/aegis_aes/aegis_aes.sv | uncovered=350 | ranges=96-162, 28-92, 530-546, 384-398, 269-280, 456-466, 211-219, 237-245

### sentinel_hmac
- duts/sentinel_hmac/sentinel_hmac.sv | uncovered=282 | ranges=45-77, 542-558, 730-741, 29-39, 307-315, 346-353, 746-753, 764-771

### rampart_i2c
- duts/rampart_i2c/rampart_i2c.sv | uncovered=493 | ranges=748-775, 953-970, 851-867, 1118-1133, 1090-1103, 1205-1218, 793-805, 1062-1072
