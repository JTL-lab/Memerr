class MemeRatings:
    def __init__(self, meme_id):
        self.meme_id = meme_id
        self.meme_ratings = []

    def add_meme_rating(self, meme_rating):
        self.meme_ratings.append(meme_rating)

    def get_all_ratings(self):
        return self.meme_ratings


class MemeRating:
    def __init__(self, meme_rating_id, ratings_by_category):
        self.meme_rating_id = meme_rating_id
        self.ratings_by_category = ratings_by_category


class RatingsByCategory:
    def __init__(self, humor, originality, relatability):
        self.humor = humor
        self.originality = originality
        self.relatability = relatability
