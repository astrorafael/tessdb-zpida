-- This is the database counterpart of a configuration file
-- All configurations are stored here

CREATE TABLE IF NOT EXISTS config_t
(
    section        TEXT NOT NULL,  -- Configuration section
    property       TEXT NOT NULL,  -- Property name
    value          TEXT NOT NULL,  -- Property value

    PRIMARY KEY(section, property)
);

CREATE TABLE IF NOT EXISTS ida_summary_t
(
	filename    		TEXT NOT NULL,  	-- Filename where the summary row comes from
    name                TEXT NOT NULL,      -- Reportedly photometer name reported by TESSDB
    mac                 TEXT,               -- Reportedly MAC Address in IDA header by TESSDB
    timezone            TEXT,               -- Reportedly Timezone zone in IDA header by TESSDB
    t0        			TIMESTAMP NOT NULL,	-- Timestamp of first valid IDA reading
    t1        			TIMESTAMP NOT NULL,	-- Timestamp of last valid IDA reading
    valid_rows 			INTEGER NOT NULL,  	-- number of rows with valid ZP / Freq / Magnitude data
    data_rows  			INTEGER NOT NULL,  	-- number of scanned rows in the summary file (>= valid_rows)
	computed_zp_median  REAL NOT NULL, 		-- Median of computed ZP given frequencies and magnitudes
	computed_zp_stdev	REAL NOT NULL, 		-- Estimated standard deviation of computed ZP
	computed_zp_max		REAL NOT NULL, 		-- Maximum computed ZP in the IDA file 
	computed_zp_min 	REAL NOT NULL, 		-- Maximum computed ZP in the IDA file 
	tessdb_zp_median	REAL NOT NULL, 		-- ZP as reported by TESSDB (median of IDA file)
	tessdb_zp_stdev		REAL NOT NULL, 		-- Std dev of reported ZP by TESSDB (normally 0.0)

    PRIMARY KEY(filename)
);
