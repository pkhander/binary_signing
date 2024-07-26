#!/usr/bin/env python3
"""
Python library for signing and notarizing binaries.

This library supports different signing processes:
1. Mac signing: Signs and notarizes macOS binaries using a Mac VM.
TODO: 2. Windows signing: (Not yet implemented) Will copy signing script to Windows host for signing.
TODO: 3. GPG signing: (Not yet implemented) Will create checksum files for binaries.

Usage as a script:
  python3 sign_binaries.py <config_file> --unsigned-digest <digest> --signing-type <type>

Where:
  <config_file>: Path to JSON configuration file
  <digest>: Digest of the unsigned binaries
  <type>: Signing type (currently only 'mac' is supported)
"""

import argparse
import json
import logging
import sys
from ssh_client import SSHClient
from common import pull_binaries, push_signed_binaries
from mac_signing import mac_signing, MAC_REQUIRED_FIELDS
from win_signing import win_signing, WIN_REQUIRED_FIELDS
from gpg_signing import gpg_signing, GPG_REQUIRED_FIELDS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

DEFAULT_REQUIRED_FIELDS = ['oci_registry_repo', 'quay_username', 'quay_password']

def load_config(config_file, signing_type):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in configuration file.")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("Configuration file not found.")
        sys.exit(1)
    
    required_fields = DEFAULT_REQUIRED_FIELDS + ['ssh_config']
    if signing_type == 'mac':
        required_fields += MAC_REQUIRED_FIELDS
    elif signing_type == 'win':
        required_fields += WIN_REQUIRED_FIELDS
    elif signing_type == 'gpg':
        required_fields += GPG_REQUIRED_FIELDS
    else:
        logger.error(f"Unknown signing type: {signing_type}")
        sys.exit(1)
    
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        logger.error(f"The following required fields are missing in the configuration file: {', '.join(missing_fields)}")
        sys.exit(1)
    
    if signing_type not in config['ssh_config']:
        logger.error(f"SSH configuration for {signing_type} is missing")
        sys.exit(1)
    
    return config

def parse_arguments():
    parser = argparse.ArgumentParser(description="Sign and notarize binaries")
    parser.add_argument("config_file", help="Path to the JSON configuration file with secrets")
    parser.add_argument("--unsigned-digest", required=True, help="Digest of the unsigned binaries")
    parser.add_argument("--signing-type", required=True, choices=['mac', 'win', 'gpg'], help="Type of signing to perform")
    return parser.parse_args()

def main():
    args = parse_arguments()
    config = load_config(args.config_file, args.signing_type)
    config['unsigned_digest'] = args.unsigned_digest

    ssh_config = config['ssh_config'][args.signing_type]
    
    try:
        with SSHClient(ssh_config['host'], ssh_config['user'], ssh_config['password']) as ssh:
            logger.info("Pulling unsigned binaries...")
            pull_binaries(ssh, config['oci_registry_repo'], config['unsigned_digest'], config['quay_username'], config['quay_password'])

            if args.signing_type == 'mac':
                mac_signing(ssh, config)
            elif args.signing_type == 'win':
                win_signing(ssh, config)
            elif args.signing_type == 'gpg':
                gpg_signing(ssh, config)
            
            logger.info("Pushing signed binaries...")
            digest = push_signed_binaries(ssh, config['oci_registry_repo'], '~/signed')
            
            logger.info(f"Signing process completed. Digest: {digest}")
    except Exception as e:
        logger.exception("An error occurred during the signing process")
        sys.exit(1)

if __name__ == "__main__":
    main()

