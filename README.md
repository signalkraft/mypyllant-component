# myPyllant Home Assistant Component

[![PyPI](https://img.shields.io/pypi/v/myPyllant)](https://pypi.org/project/myPyllant/)

Home Assistant component that interfacts with the myVAILLANT API using the [myPyllant library](https://github.com/signalkraft/mypyllant).

![myPyllant](https://raw.githubusercontent.com/signalkraft/myPyllant/main/logo.png)

**Alpha, tested on an aroTHERM plus heatpump, sensoCOMFORT VRC 720, and sensoNET VR 921.**

Not affiliated with Vaillant, the developers take no responsibility for anything that happens to your Vaillant devices because of this library.

## Features

![Screenshot](https://raw.githubusercontent.com/signalkraft/mypyllant-component/main/screenshot.png)

* Supports climate & hot water controls, as well as sensor information
* Control operating modes, target temperature, and presets such as holiday more or quick veto
* Track sensor information of devices, such as temperature, humidity, operating mode, or energy usage
* See diagnostic information, such as the current heating curve, or water pressure

## Installation
1. [Install HACS](https://hacs.xyz/docs/setup/download)
1. Add `https://github.com/signalkraft/mypyllant-component` as a [custom repository in HACS > Integrations](https://hacs.xyz/docs/faq/custom_repositories)
1. Open the myVAILLANT integration in HACS and install it
1. Go to Settings > Integrations and add myVAILLANT
1. Sign in with the email & password you use in the myVAILLANT app
