# Code Watchman Python Library

## Overview

Code Watchman is a powerful logging and monitoring system designed for developers and small teams. This Python library allows you to seamlessly integrate Code Watchman's functionality into your Python applications, enabling real-time insights, instant alerts, and flexible monitoring of your code's performance.

## Features

- Real-time logging and monitoring
- Instant alerts for critical events
- Flexible integration with your existing codebase
- Mobile access to your logs and notifications
- Team collaboration tools

## Installation

Install the Code Watchman Python library using pip:

```
pip install codewatchman
```

## Usage

### With a Code Watchman Account

1. Download the Code Watchman mobile app from the App Store or Google Play Store
2. Create an account and a new project within the app
3. Obtain your API key and secret from the project settings in the mobile app
4. Initialize the Code Watchman logger in your Python code:

```python
from codewatchman import CodeWatchman

logger = CodeWatchman(
    name="my_app",
    level="INFO",
    project_id="YOUR_PROJECT_ID",
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET"
)
```

5. Use the logger to send logs and notifications:

```python
logger.info("Application started")
logger.error("An error occurred", exc_info=True)
logger.notify("Critical issue detected", priority="high")
```

### Without a Code Watchman Account

The Code Watchman library can also be used as a standalone logging solution without connecting to the Code Watchman service:

```python
from codewatchman import CodeWatchman

logger = CodeWatchman(
    name="my_app",
    level="INFO"
)

logger.info("This log will be handled locally")
```

When used without an account, logs will be processed according to your local configuration (e.g., written to a file or console).

## Configuration

The `CodeWatchman` class accepts the following parameters:

- `name`: The name of your application or component
- `level`: The logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
- `project_id`: The ID of your project (obtained from the mobile app)
- `api_key`: Your Code Watchman API key (obtained from the mobile app)
- `api_secret`: Your Code Watchman API secret (obtained from the mobile app)

## Additional Documentation

For more detailed information on using the Code Watchman Python library, including advanced features and customization options, please visit our [official documentation](https://docs.codewatchman.com).

## Support

If you encounter any issues or have questions about using the Code Watchman Python library, please don't hesitate to contact our support team through the mobile app or open an issue in this repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.