#include <stdio.h>
#include <libfreenect/libfreenect.h>

int main()
{
	freenect_context *context;
	int ret = freenect_init(&context, NULL);
	if (ret)
	{
		printf("Couldn't initialize the Freenect driver.\n");
		return -1;
	}

	printf("Successfully initialized the Freenect driver.  Detected %d currently-attached device(s).\n", freenect_num_devices(context));

	ret = freenect_shutdown(context);
	if (ret)
	{
		printf("Couldn't shut down the Freenect driver.\n");
		return -1;
	}

	return 0;
}
