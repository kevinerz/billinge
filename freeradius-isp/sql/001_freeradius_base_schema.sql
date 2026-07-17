-- Vendored stock FreeRADIUS 3.2.x MySQL schema (rlm_sql main tables), based on
-- raddb/mods-config/sql/main/mysql/schema.sql from the upstream 3.2 branch.
-- Intentionally unmodified here — tenant scoping is layered on top in
-- 003_add_tenant_id_columns.sql so upgrades against upstream stay traceable.

CREATE TABLE radcheck (
  id           int(11) unsigned NOT NULL auto_increment,
  username     varchar(64) NOT NULL DEFAULT '',
  attribute    varchar(64) NOT NULL DEFAULT '',
  op           char(2) NOT NULL DEFAULT '==',
  value        varchar(253) NOT NULL DEFAULT '',
  PRIMARY KEY (id),
  KEY username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE radreply (
  id           int(11) unsigned NOT NULL auto_increment,
  username     varchar(64) NOT NULL DEFAULT '',
  attribute    varchar(64) NOT NULL DEFAULT '',
  op           char(2) NOT NULL DEFAULT '=',
  value        varchar(253) NOT NULL DEFAULT '',
  PRIMARY KEY (id),
  KEY username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE radgroupcheck (
  id           int(11) unsigned NOT NULL auto_increment,
  groupname    varchar(64) NOT NULL DEFAULT '',
  attribute    varchar(64) NOT NULL DEFAULT '',
  op           char(2) NOT NULL DEFAULT '==',
  value        varchar(253) NOT NULL DEFAULT '',
  PRIMARY KEY (id),
  KEY groupname (groupname)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE radgroupreply (
  id           int(11) unsigned NOT NULL auto_increment,
  groupname    varchar(64) NOT NULL DEFAULT '',
  attribute    varchar(64) NOT NULL DEFAULT '',
  op           char(2) NOT NULL DEFAULT '=',
  value        varchar(253) NOT NULL DEFAULT '',
  PRIMARY KEY (id),
  KEY groupname (groupname)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE radusergroup (
  username     varchar(64) NOT NULL DEFAULT '',
  groupname    varchar(64) NOT NULL DEFAULT '',
  priority     int(11) NOT NULL DEFAULT 1,
  KEY username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE radacct (
  radacctid           bigint(21) NOT NULL auto_increment,
  acctsessionid       varchar(64) NOT NULL DEFAULT '',
  acctuniqueid        varchar(32) NOT NULL DEFAULT '',
  username            varchar(64) NOT NULL DEFAULT '',
  groupname           varchar(64) NOT NULL DEFAULT '',
  realm               varchar(64) DEFAULT '',
  nasipaddress        varchar(15) NOT NULL DEFAULT '',
  nasportid           varchar(32) DEFAULT NULL,
  nasporttype         varchar(32) DEFAULT NULL,
  acctstarttime       datetime DEFAULT NULL,
  acctupdatetime      datetime DEFAULT NULL,
  acctstoptime        datetime DEFAULT NULL,
  acctinterval        bigint(12) DEFAULT NULL,
  acctsessiontime     bigint(12) unsigned DEFAULT NULL,
  acctauthentic       varchar(32) DEFAULT NULL,
  connectinfo_start   varchar(50) DEFAULT NULL,
  connectinfo_stop    varchar(50) DEFAULT NULL,
  acctinputoctets     bigint(20) DEFAULT NULL,
  acctoutputoctets    bigint(20) DEFAULT NULL,
  calledstationid     varchar(50) NOT NULL DEFAULT '',
  callingstationid    varchar(50) NOT NULL DEFAULT '',
  acctterminatecause  varchar(32) NOT NULL DEFAULT '',
  servicetype         varchar(32) DEFAULT NULL,
  framedprotocol      varchar(32) DEFAULT NULL,
  framedipaddress     varchar(15) NOT NULL DEFAULT '',
  PRIMARY KEY (radacctid),
  KEY username (username),
  KEY framedipaddress (framedipaddress),
  KEY acctsessionid (acctsessionid),
  KEY acctuniqueid (acctuniqueid),
  KEY acctstarttime (acctstarttime),
  KEY acctstoptime (acctstoptime),
  KEY nasipaddress (nasipaddress)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE radpostauth (
  id           int(11) NOT NULL auto_increment,
  username     varchar(64) NOT NULL DEFAULT '',
  pass         varchar(64) NOT NULL DEFAULT '',
  reply        varchar(32) NOT NULL DEFAULT '',
  authdate     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  class        varchar(64) DEFAULT '',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE nas (
  id           int(10) NOT NULL auto_increment,
  nasname      varchar(128) NOT NULL,
  shortname    varchar(32) DEFAULT NULL,
  type         varchar(30) DEFAULT 'other',
  ports        int(5) DEFAULT NULL,
  secret       varchar(60) NOT NULL DEFAULT 'secret',
  server       varchar(64) DEFAULT NULL,
  community    varchar(50) DEFAULT NULL,
  description  varchar(200) DEFAULT 'RADIUS Client',
  PRIMARY KEY (id),
  UNIQUE KEY nasname (nasname)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE radippool (
  id                int(11) unsigned NOT NULL auto_increment,
  pool_name         varchar(30) NOT NULL,
  framedipaddress   varchar(15) NOT NULL DEFAULT '',
  nasipaddress      varchar(15) NOT NULL DEFAULT '',
  calledstationid   varchar(30) NOT NULL,
  callingstationid  varchar(30) NOT NULL,
  expiry_time       datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  username          varchar(64) NOT NULL DEFAULT '',
  pool_key          varchar(30) NOT NULL DEFAULT '',
  PRIMARY KEY (id),
  KEY framedipaddress (framedipaddress),
  KEY pool_name (pool_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
