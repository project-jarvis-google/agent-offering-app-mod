import { Box } from '@mui/material';
import { styled, darken } from '@mui/material/styles';

const shimmerAnimation = `
  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }
`;

const ShimmerContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  overflow: 'hidden',
  width: '100%',
  display: 'flex',
  flexDirection: 'column',
  gap: '12px',
  '&::after': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    transform: 'translateX(-100%)',
    backgroundImage: `linear-gradient(90deg, 
      transparent, 
      ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)'}, 
      transparent)`,
    animation: 'shimmer 1.5s infinite',
  },
}));

const ShimmerBar = styled('div')(({ theme }) => ({
  height: '24px',
  borderRadius: '8px',
  backgroundColor: darken(theme.palette.action.hover, theme.palette.mode === 'dark' ? 0.3 : 0.05),
}));

const ShimmerLoader = () => {
  return (
    <>
      <style>{shimmerAnimation}</style>
      <ShimmerContainer>
        <ShimmerBar style={{ width: '95%' }} />
        <ShimmerBar style={{ width: '100%' }} />
        <ShimmerBar style={{ width: '98%' }} />
        <ShimmerBar style={{ width: '90%' }} />
        <ShimmerBar style={{ width: '100%' }} />
        <ShimmerBar style={{ width: '85%' }} />
      </ShimmerContainer>
    </>
  );
};

export default ShimmerLoader;
