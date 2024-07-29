#!/usr/bin/env python3

def pull_content_using_oras(ssh, registry, digest, username, password, target_dir='/Users/macos-signing/pk-testing/unsigned/'):
    """Pull binaries using oras with authentication"""
    env_vars = f"export ORAS_USERNAME='{username}' && export ORAS_PASSWORD='{password}'"
    cd_command = f"mkdir -p {target_dir} && cd {target_dir} && "
    pull_command = f"/Users/macos-signing/pk-testing/oras pull {registry}@{digest}"
    ssh.run_command(env_vars, sensitive=True)
    ssh.run_command(cd_command, sensitive=True)
    return ssh.run_command(pull_command)

def push_content_using_oras(ssh, registry, signed_dir):
    """Push signed binaries to OCI registry"""
    command = f"oras push {registry} {signed_dir}/*.app"
    output, _ = ssh.run_command(command)
    digest = next((line.split()[1] for line in output.splitlines() if line.startswith('Digest:')), None)
    return digest
