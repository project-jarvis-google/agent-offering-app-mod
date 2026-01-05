import React from "react";
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Avatar,
  Link,
} from "@mui/material";
import LinkedInIcon from "@mui/icons-material/LinkedIn";

const teamMembers = [
  {
    name: "Jane Doe",
    role: "Lead Frontend Developer",
    avatarUrl: "/path/to/jane-avatar.jpg",
    linkedIn: "https://www.linkedin.com/in/janedoe",
  },
  {
    name: "John Smith",
    role: "Backend & Cloud Architect",
    avatarUrl: "/path/to/john-avatar.jpg",
    linkedIn: "https://www.linkedin.com/in/johnsmith",
  },
  {
    name: "Alex Ray",
    role: "UI/UX Designer",
    avatarUrl: "/path/to/alex-avatar.jpg",
    linkedIn: "https://www.linkedin.com/in/alexray",
  },
];

const AboutPage: React.FC = () => {
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography
        variant="h3"
        component="h1"
        gutterBottom
        textAlign="center"
        fontWeight="bold"
      >
        Meet the Team
      </Typography>
      <Typography
        variant="h6"
        color="text.secondary"
        textAlign="center"
        sx={{ mb: 6 }}
      >
        The dedicated individuals who brought SPARC to life.
      </Typography>

      <Grid container spacing={4} justifyContent="center">
        {teamMembers.map((member) => (
          <Grid
            item
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            {...({ xs: 12, sm: 6, md: 4 } as any)}
            key={member.name}
          >
            <Card
              sx={{
                textAlign: "center",
                height: "100%",
                borderRadius: "16px",
                boxShadow: 3,
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Avatar
                  alt={member.name}
                  src={member.avatarUrl}
                  sx={{
                    width: 100,
                    height: 100,
                    margin: "0 auto 16px",
                    bgcolor: "primary.main",
                  }}
                >
                  {member.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </Avatar>
                <Typography variant="h6" component="h2" fontWeight="bold">
                  {member.name}
                </Typography>
                <Typography color="text.secondary" sx={{ mb: 2 }}>
                  {member.role}
                </Typography>
                <Link
                  href={member.linkedIn}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <LinkedInIcon color="primary" />
                </Link>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default AboutPage;
