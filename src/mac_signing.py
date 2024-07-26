#!/usr/bin/env python3

MAC_REQUIRED_FIELDS = [
    'mac_vm_ip', 'mac_vm_user', 'mac_vm_password', 'keychain_password',
    'signing_identity', 'notarization_username', 'notarization_password'
]

def unlock_keychain(ssh, keychain_password):
    """Unlock security keychain"""
    return ssh.run_command(f"security unlock-keychain -p {keychain_password} login.keychain", sensitive=True)

def sign_binaries(ssh, signing_identity):
    """Sign binaries using codesign"""
    return ssh.run_command(f"codesign --force --options runtime --sign '{signing_identity}' *.app")

def notarize_binaries(ssh, username, password):
    """Notarize binaries using altool"""
    command = (f"xcrun altool --notarize-app --primary-bundle-id 'com.example.app' "
               f"--username '{username}' --password '{password}' "
               f"--file app.zip")
    return ssh.run_command(command)

def remove_binaries(ssh):
    """Remove binaries from Mac VM"""
    return ssh.run_command("rm -rf *.app ~/signed")

def mac_signing(ssh, config):
    try:
        unlock_keychain(ssh, config['keychain_password'])
        sign_binaries(ssh, config['signing_identity'])
        notarize_binaries(ssh, config['notarization_username'], config['notarization_password'])
        remove_binaries(ssh)
    except Exception as e:
        logger.exception("An error occurred during the Mac signing process")
        raise
