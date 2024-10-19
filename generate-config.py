import argparse
from piawg import piawg
from datetime import datetime
import os

def print_locations(pia):
    print("Available PIA server locations:")
    for location in sorted(pia.server_list.keys()):
        print(f"  {location}")

def main():
    # subparsers for generate & get locations
    parser = argparse.ArgumentParser(description="Generate PIA WireGuard configuration")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Subparser for get-locations
    get_locations_parser = subparsers.add_parser('get-locations', help="Print all available PIA Wireguard server locations")

    # Subparser for generate
    generate_parser = subparsers.add_parser('generate', help="Used to generate the Wireguard configuration file")
    generate_parser.add_argument("--username", required=True, help="PIA username")
    generate_parser.add_argument("--password", required=True, help="PIA password")
    generate_parser.add_argument("--location", required=True, help="PIA server location (i.e., UK-London or 'UK London')")
    generate_parser.add_argument("--output-dir", help="Directory to save the configuration file (i.e. /etc/wireguard/, default: current directory)")

    args = parser.parse_args()

    pia = piawg()

    if args.command == 'get-locations':
        print_locations(pia)
        return

    if args.command == 'generate':
        # Set region
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

        # guild config
        config_filename = 'pia.conf'
        
        # save to the specified output directory or the current directory
        output_dir = args.output_dir if args.output_dir else os.getcwd()
        config_path = os.path.join(output_dir, config_filename)

        # check the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        print(f"Saving configuration file: {config_path}")
        
        # get current time for the comment
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(config_path, 'w') as file:
            file.write(f"# configuration generated on {current_time}\n\n")
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
