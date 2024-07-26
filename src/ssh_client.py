import paramiko
import logging

logger = logging.getLogger(__name__)

class SSHClient:
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.client = None

    def __enter__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(self.hostname, username=self.username, password=self.password)
            logger.info(f"Successfully connected to {self.hostname}")
        except paramiko.AuthenticationException:
            logger.error(f"Authentication failed when connecting to {self.hostname}")
            raise
        except paramiko.SSHException as e:
            logger.error(f"Failed to connect to {self.hostname}: {e}")
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()
            logger.info(f"Connection to {self.hostname} closed")

    def run_command(self, command, sensitive=False):
        """Run command on remote server via SSH and log the output"""
        if not sensitive:
            logger.info(f"Running command: {command}")
        
        stdin, stdout, stderr = self.client.exec_command(command)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        
        if not sensitive:
            if out:
                logger.info(f"Command output: {out}")
            if err:
                logger.error(f"Command error: {err}")
        
        return out, err
