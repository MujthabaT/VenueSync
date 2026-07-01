output "EC2_PUBLIC_IP" {
  description = "Public IP of VenueSync server"
  value       = aws_instance.venuesync_server.public_ip
}

output "EC2_PUBLIC_DNS" {
  description = "Public DNS of server"
  value       = aws_instance.venuesync_server.public_dns
}
