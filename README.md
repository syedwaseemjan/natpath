# natpath

A read-only command that tells you when private subnets send S3 and DynamoDB traffic through a NAT gateway.

NAT data processing is billed for every byte. The gateway endpoints for S3 and DynamoDB are free. They add a route for those two services, so that traffic never reaches the NAT. Traffic to the rest of the internet still does. If the route table behind the NAT does not have those endpoints, S3 and DynamoDB bytes from those subnets are on the NAT bill. The cost page shows the amount. This command shows the route tables and subnets that cause it.

You run it, add the missing gateway endpoints on the printed route tables, and run it again until it prints nothing.
