import argparse
import configparser
import json
import logging
import os
import sys

from sync import constants, sync, oauth2, integrations

DEFAULT_CONFIG_PATH = "config.ini"


def ReadConfig(filename):
    """Reads and returns the ConfigParser instance."""
    config = configparser.RawConfigParser()
    config.read(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), filename))
    return config


def CommandSync(config, args):
    """Cleanup and do syncing of products."""
    sync.DoCleanupProcedure(config)
    sync.DoSyncProcedure(config, read_only=args.readonly)


def CommandReauthenticate(config, args):
    """Refresh authentication token."""
    DoLazadaResetAccessToken(config, args.token)


def CommandCleanup(config, args):
    """Cleanup dangling data."""
    sync.DoCleanupProcedure(config)


def CommandCheckConfig(config, args):
    """Check if auth config is still working."""
    logging.info(config.sections())
    oauth2_service = oauth2.Oauth2Service(dbpath=config.get("Common", "Store"))
    with oauth2_service:
        lazada_oauth2_dict = oauth2_service.GetOauth2Tokens(
            constants._SYSTEM_LAZADA)
        logging.info(lazada_oauth2_dict)


def CommandSandbox(config, args):
    """Free-for-all testing func."""
    shopee_client = integrations.shopee.ShopeeClient(
        shop_id=config.getint("Shopee", "ShopID"),
        partner_id=config.getint("Shopee", "PartnerID"),
        partner_key=config.get("Shopee", "PartnerKey"),
        with_refresh=False)

    item_id = 1295544772  # sku: CPLA175RRD
    try:
        result = shopee_client._Request(
            "/api/v1/item/get",
            shopee_client._ConstructPayload({"item_id": item_id}))
    except ValueError as e:
        logging.info(e)

    # See `dumps/shopee.json` for example output.
    logging.info(json.dumps(result.result, indent=4))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Command name to function mapping.
    COMMAND_LOOKUP = {
        "sync": CommandSync,
        "lzreauth": CommandReauthenticate,
        "cleanup": CommandCleanup,
        "chkconfig": CommandCheckConfig,
        "sandbox": CommandSandbox,
    }

    # Setup argument parser.
    parser = argparse.ArgumentParser(
        description="Opencart-Lazada-Shopee syncing script.")
    parser.add_argument(
        "mode",
        choices=COMMAND_LOOKUP.keys(),
        action="store",
        help="OCLZSH syncing script mode",
    )
    parser.add_argument(
        "--config",
        action="store",
        default=os.getenv("CONFIG_PATH", DEFAULT_CONFIG_PATH),
        help="path of the config file",
    )
    parser.add_argument(
        "--token",
        action="store",
        default="",
        help="token to use when reauthenticating to Lazada",
    )
    parser.add_argument(
        "--readonly",
        action="store_true",
        default=False,
        help="set to true to only read but not write",
    )
    args = parser.parse_args(sys.argv[1:])

    # Setup config path.
    config = ReadConfig(args.config)

    # Invoke action based on matching mode.
    COMMAND_LOOKUP[args.mode](config, args)
