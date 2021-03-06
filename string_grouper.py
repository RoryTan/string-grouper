from sklearn.feature_extraction.text import TfidfVectorizer
from ftfy import fix_text
from tqdm import tqdm
import re


class String_Grouper:

    """

    Base class for string grouping algo

    """

    def __init__(self, strings_to_group: list, new_matrix=None):

        self.strings_to_group = strings_to_group

        self.vectorizer = TfidfVectorizer(analyzer=self.ngrams)

        self.original_matrix = self.vectorizer.fit_transform(self.strings_to_group)

    @staticmethod
    def ngrams(string, n=3):

        """

        Takes an input string, cleans it and converts to ngrams.

        """

        string = str(string)

        string = string.lower()  # lower case

        string = fix_text(string)  # fix text

        string = string.encode(
            "ascii", errors="ignore"
        ).decode()  # remove non ascii chars

        chars_to_remove = [")", "(", ".", "|", "[", "]", "{", "}", "'", "-"]

        rx = (
            "[" + re.escape("".join(chars_to_remove)) + "]"
        )  # remove punc, brackets etc...

        string = re.sub(rx, "", string)

        string = string.replace("&", "and")

        string = string.title()  # normalise case - capital at start of each word

        string = re.sub(
            " +", " ", string
        ).strip()  # get rid of multiple spaces and replace with a single

        string = " " + string + " "  # pad names for ngrams...

        ngrams = zip(*[string[i:] for i in range(n)])

        return ["".join(ngram) for ngram in ngrams]

    def cosine_pairwise_distance_to_coo(self, new_matrix):

        """

        Calculates cosine similarity of the fitted sparse matrix & the new matrix with a default threshold of 0.80

        """

        cosine_matrix = sklearn.metrics.pairwise.cosine_similarity(
            self.original_matrix, new_matrix, dense_output=False
        )

        return cosine_matrix.tocoo()  # Convert Sparse Matrix to COO to tuple unpack

    def group_on_self(self, cosine_threshold_score=0.80):

        """

        Wrapper function that performs distance calculation and filtering on the same corpus

        """

        new_matrix = self.vectorizer.transform(self.strings_to_group)

        print("Done Transforming New Matrix")

        coo_matrix = self.cosine_pairwise_distance_to_coo(
            new_matrix
        )  # calculate pairwise distance between fitted & test set

        print("Done Calculating Distance")

        coo_tup = zip(
            coo_matrix.row, coo_matrix.col, coo_matrix.data
        )  # zip up key objects

        print("Starting to filter")

        filtered_coo = [
            (r, c, d) for r, c, d in tqdm(coo_tup) if d > cosine_threshold_score
        ]  # [filter_coo(tup) for tup in coo_tup]

        print("Reconstituting COO to DataFrame")

        return self.reconsitute_from_idx(
            self.strings_to_group, self.strings_to_group, filtered_coo
        )

    @staticmethod
    def reconstitute_from_idx(original_list, matched_list, coo_tup):

        """

        Reconstitute the a dataframe from 2 lists, and the COO matrix index

        """

        names = ["group_name", "alias", "score"]

        return pd.DataFrame(
            [(original_list[i], matched_list[j], s) for i, j, s in coo_tup],
            columns=names,
        )
