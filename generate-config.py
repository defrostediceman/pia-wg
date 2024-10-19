import argparse
from piawg import piawg
from datetime import datetime
import os

# added function to print pia server locations as a non mandatory argument.
def print_locations(pia):
    print("Available PIA server locations:")
    for location in sorted(pia.server_list.keys()):
        print(f"  {location}")

def main():
    # add arguments to allow the script to be used 'non-interactively'
    parser = argparse.ArgumentParser(description="Generate PIA WireGuard configuration")
    parser.add_argument("--username", required=True, help="PIA username")
    parser.add_argument("--password", required=True, help="PIA password")
    parser.add_argument("--location", required=True, help="PIA server location (e.g., UK-London)")
    parser.add_argument("--get-locations", action="store_true", help="Print all available locations and exit")
    parser.add_argument("--output-dir", help="Directory to save the configuration file (default: current directory)")
    args = parser.parse_args()

    pia = piawg()

    # get server locations run first to allow to be ran alone.
    if args.get_locations:
        print_locations(pia)
        return

    # set region, could add the ability to regex against the out of print_locations()
    location = args.location.replace('-', ' ')
    if location not in pia.server_list:
        print(f"Error: '{location}' is not a valid location.")
        print_locations(pia)
        return

    # generate public and private key pair
    pia.generate_keys()

    pia.set_region(location)
    print(f"Selected '{location}'")

    # get token
    if pia.get_token(args.username, args.password):
        print("Login successful!")
    else:
        print("Error logging in. Please check your credentials.")
        return

    # add key
    status, response = pia.addkey()
    if status:
        print("Added key to server!")
    else:
        print("Error adding key to server")
        print(response)
        return

    # build config, changed to pia.conf for ease of configuration
    config_filename = 'pia.conf'
    
    # use the specified output directory or the current directory
    output_dir = args.output_dir if args.output_dir else os.getcwd()
    config_path = os.path.join(output_dir, config_filename)

    # check the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print(f"Saving configuration file: {config_path}")
    
    # get current time for the config comment
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # generate configuration
    with open(config_path, 'w') as file:
        file.write(f"# PIA WireGuard configuration generated on {current_time}\n\n")
        file.write('[Interface]\n')
        file.write(f'Address = {pia.connection["peer_ip"]}\n')
        file.write(f'PrivateKey = {pia.privatekey}\n')
        file.write(f'DNS = {pia.connection["dns_servers"][0]},{pia.connection["dns_servers"][1]}\n\n')
        file.write('[Peer]\n')
        file.write(f'PublicKey = {pia.connection["server_key"]}\n')
        file.write(f'Endpoint = {pia.connection["server_ip"]}:1337\n')
        file.write('AllowedIPs = 0.0.0.0/0\n')
        file.write('PersistentKeepalive = 25\n')

if __name__ == "__main__":
    main()
