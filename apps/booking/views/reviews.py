from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from apps.booking.models import Review
from apps.booking.serializers import CreateReviewSerializer, ReviewSerializer
from apps.booking.permissions import IsOwner



class ReviewListCreateView(generics.ListCreateAPIView):
    """GET все отзывы, POST создать отзыв"""
    queryset = Review.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return CreateReviewSerializer if self.request.method == 'POST' else ReviewSerializer

    def get_queryset(self):
        qs = Review.objects.all()
        if listing_id := self.request.query_params.get('listing'):
            try:
                qs = qs.filter(listing_id=int(listing_id))
            except:
                pass
        return qs

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE конкретного отзыва"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwner]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_reviews(request):
    """Мои отзывы"""
    from apps.booking.serializers import ReviewSerializer
    reviews = Review.objects.filter(reviewer=request.user)
    return Response(ReviewSerializer(reviews, many=True).data)
