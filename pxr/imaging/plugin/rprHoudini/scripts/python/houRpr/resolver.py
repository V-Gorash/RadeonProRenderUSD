from pxr import Plug, Tf
from time import sleep

import hou
import os

usd_plugin = Plug.Registry().GetPluginWithName('RenderStudioResolver')
if not usd_plugin.isLoaded:
    usd_plugin.Load()

from rs import RenderStudioKit

shared_workspace_enabled = False


def workspace_enabled_callback(notice, sender):
    global shared_workspace_enabled
    shared_workspace_enabled = notice.IsConnected()

def workspace_state_callback(notice, sender):
    hou.ui.displayMessage(str(notice.GetState()),
                          severity=hou.severityType.Warning)


listener_1 = Tf.Notice.RegisterGlobally("RenderStudioNotice::WorkspaceConnectionChanged", workspace_enabled_callback)
# listener_3 = Tf.Notice.RegisterGlobally("RenderStudioNotice::WorkspaceState", workspace_state_callback)

def get_shared_workspace_menu():
    global shared_workspace_enabled
    if shared_workspace_enabled:
        return ["disable", "Disconnect from Render Studio shared workspace"]
    else:
        return ["enable", "Connect to Render Studio shared workspace"]


def toggle_shared_workspace(command):
    global shared_workspace_enabled

    if command == "enable":
        code, server_url = hou.ui.readInput("Storage server URL", buttons=('OK',),
                                            severity=hou.severityType.Message, help=None, title=None,
                                            initial_contents=RenderStudioKit.GetWorkspaceUrl())
        if code == -1 or server_url == "":
            return
        if not server_url.startswith("http"):
            hou.ui.displayMessage("The URL should start from 'http://' or 'https://'",
                                  severity=hou.severityType.Warning)
            toggle_shared_workspace("enable")
            return
        try:
            with hou.InterruptableOperation("Connecting to shared workspace", open_interrupt_dialog=True) as op:
                RenderStudioKit.SetWorkspaceUrl(server_url)
                RenderStudioKit.SharedWorkspaceConnect()
        except hou.OperationInterrupted:
            toggle_shared_workspace("disable")
        except:
            toggle_shared_workspace("disable")
            raise Exception('Shared workspace server is unavailable')
    else:
        try:
            with hou.InterruptableOperation("Disconnecting from shared workspace", open_interrupt_dialog=True) as op:
                RenderStudioKit.SharedWorkspaceDisconnect()
        except hou.OperationInterrupted:
            pass
        except:
            raise Exception('Error on shared workspace disconnecting')


def set_workspace_directory():
    directory = hou.ui.selectFile(
        title='Render Studio Workspace Directory',
        start_directory=RenderStudioKit.GetWorkspacePath().replace('\\', '/'),
        file_type=hou.fileType.Directory,
        chooser_mode=hou.fileChooserMode.Write)
    if directory:
        RenderStudioKit.SetWorkspacePath(hou.expandString(directory))

def get_workspace_directory():
    return RenderStudioKit.GetWorkspacePath().replace('\\', '/')

def open_workspace_directory():
    os.system("explorer " + RenderStudioKit.GetWorkspacePath())
