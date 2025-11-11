#!/bin/bash

################################################################################
# MariaDB Configuration Script for Frappe/ERPNext
# This script configures MariaDB with the required settings for Frappe/ERPNext
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running with sudo
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run with sudo privileges"
   exit 1
fi

log_info "Configuring MariaDB for Frappe/ERPNext..."

# Backup existing configuration
MARIADB_CONFIG="/etc/mysql/mariadb.conf.d/50-server.cnf"
BACKUP_FILE="${MARIADB_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

if [ -f "$MARIADB_CONFIG" ]; then
    log_info "Backing up existing configuration to: $BACKUP_FILE"
    cp "$MARIADB_CONFIG" "$BACKUP_FILE"
fi

# Create new configuration
log_info "Writing new MariaDB configuration..."
cat > "$MARIADB_CONFIG" << 'EOF'
#
# These groups are read by MariaDB server.
# Use it for options that only the server (but not clients) should see

# this is read by the standalone daemon and embedded servers
[server]
user = mysql
pid-file = /run/mysqld/mysqld.pid
socket = /run/mysqld/mysqld.sock
basedir = /usr
datadir = /var/lib/mysql
tmpdir = /tmp
lc-messages-dir = /usr/share/mysql
bind-address = 127.0.0.1
query_cache_size = 16M
log_error = /var/log/mysql/error.log

# this is only for the mysqld standalone daemon
[mysqld]
innodb-file-format=barracuda
innodb-file-per-table=1
innodb-large-prefix=1
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# this is only for embedded server
[embedded]

# This group is only read by MariaDB servers, not by MySQL.
# If you use the same .cnf file for MySQL and MariaDB,
# you can put MariaDB-only options here
[mariadb]

# This group is only read by MariaDB-10.5 servers.
# If you use the same .cnf file for MariaDB of different versions,
# use this group for options that older servers don't understand
[mariadb-10.5]

[mysql]
default-character-set = utf8mb4
EOF

# Restart MariaDB service
log_info "Restarting MariaDB service..."
systemctl restart mysql

# Check if MariaDB is running
if systemctl is-active --quiet mysql; then
    log_info "MariaDB is running successfully with new configuration"
else
    log_error "MariaDB failed to start. Check logs: /var/log/mysql/error.log"
    log_warn "Restoring backup configuration..."
    cp "$BACKUP_FILE" "$MARIADB_CONFIG"
    systemctl restart mysql
    exit 1
fi

log_info "=========================================="
log_info "MariaDB configuration completed!"
log_info "=========================================="
log_info ""
log_info "IMPORTANT: If you haven't already, run mysql_secure_installation:"
log_info "   sudo mysql_secure_installation"
log_info ""
log_info "Backup of previous configuration saved at:"
log_info "   $BACKUP_FILE"
log_info ""
